from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_api import DesktopApi
from divan_runtime.desktop_protocol import handle_request
from divan_runtime.execution_contract import ExecutionAction, ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.task_model import DivanTask


class FakeEngine:
    engine_id = "native"

    def __init__(self):
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        if request.action is ExecutionAction.FILE_DIFF:
            payload = {
                "diff": "diff --git a/app.py b/app.py\n+print('ok')\n",
                "staged": request.args.get("staged") is True,
            }
            argv = ("git", "diff", "--cached", "--") if payload["staged"] else (
                "git",
                "diff",
                "--",
            )
        else:
            payload = {
                "worktree": "C:/tmp/worktree",
                "agent": request.args.get("agent") or "codex",
            }
            argv = ("codex", "exec", "<redacted-prompt>")
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=True,
            exit_code=0,
            payload=payload,
            stdout="",
            stderr="",
            argv=argv,
            mandate_id=request.mandate_id,
        )


class DesktopProtocolTests(unittest.TestCase):
    def test_capabilities_response_has_envelope(self):
        response = handle_request(
            {"command": "capabilities"},
            ExecutionRouter([FakeEngine()]),
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["api_version"], 1)
        self.assertEqual(response["result"]["product"], "Divan")
        self.assertIn("task.start", response["result"]["commands"])
        self.assertIn("task.diff", response["result"]["commands"])
        self.assertIn("task.review.auto", response["result"]["commands"])

    def test_task_create_plan_start_uses_explicit_approval(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            router = ExecutionRouter([FakeEngine()], default_engine="native")
            created = handle_request(
                {"command": "task.create", "task_id": "DIV-1", "title": "Fix login"},
                router,
            )
            planned = handle_request(
                {"command": "task.plan", "task_id": "DIV-1"},
                router,
            )
            denied = handle_request(
                {"command": "task.start", "task_id": "DIV-1", "agent": "codex"},
                router,
            )
            started = handle_request(
                {
                    "command": "task.start",
                    "task_id": "DIV-1",
                    "agent": "codex",
                    "approve_execution": True,
                },
                router,
            )
            evidence = handle_request(
                {"command": "evidence.list", "task_id": "DIV-1"},
                router,
            )

            self.assertTrue(created["ok"])
            self.assertEqual(planned["result"]["state"], "planned")
            self.assertEqual(
                denied["error"]["code"],
                "DESKTOP_EXECUTION_APPROVAL_REQUIRED",
            )
            self.assertTrue(started["ok"], started)
            self.assertEqual(started["result"]["state"], "running")
            self.assertTrue(started["result"]["mandate_id"].startswith("mandate-"))
            self.assertEqual(evidence["result"][0]["kind"], "execution")
            self.assertNotIn("Fix login", str(evidence["result"][0]["data"]["argv"]))

    def test_task_diff_uses_execution_worktree_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            router = ExecutionRouter([FakeEngine()], default_engine="native")
            handle_request(
                {"command": "task.create", "task_id": "DIV-2", "title": "Edit app"},
                router,
            )
            handle_request({"command": "task.plan", "task_id": "DIV-2"}, router)
            handle_request(
                {
                    "command": "task.start",
                    "task_id": "DIV-2",
                    "agent": "codex",
                    "approve_execution": True,
                },
                router,
            )

            diff = handle_request(
                {"command": "task.diff", "task_id": "DIV-2"},
                router,
            )

            self.assertTrue(diff["ok"], diff)
            self.assertTrue(diff["result"]["ok"])
            self.assertEqual(diff["result"]["engine"], "native")
            self.assertIn("diff --git", diff["result"]["diff"])
            self.assertEqual(diff["result"]["path"], "*")
            self.assertFalse(diff["result"]["staged"])
            self.assertEqual(diff["result"]["basis"], "working-tree")

    def test_task_diff_defaults_to_reviewed_staged_snapshot_after_review(self):
        engine = FakeEngine()
        router = ExecutionRouter([engine], default_engine="native")
        task = DivanTask(
            task_id="DIV-REVIEWED",
            title="Reviewed change",
            engine_id="native",
            mandate_id="mandate-reviewed",
            metadata={
                "execution": {"payload": {"worktree": "C:/tmp/worktree"}},
                "review_snapshot": {"diff_sha256": "a" * 64},
            },
        )

        diff = DesktopApi(router).task_diff(task)

        self.assertTrue(diff["staged"])
        self.assertEqual(diff["basis"], "review-snapshot")
        self.assertTrue(engine.requests[-1].args["staged"])

    def test_task_diff_requires_an_execution_worktree(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            router = ExecutionRouter([FakeEngine()], default_engine="native")
            handle_request(
                {"command": "task.create", "task_id": "DIV-3", "title": "Edit app"},
                router,
            )

            diff = handle_request(
                {"command": "task.diff", "task_id": "DIV-3"},
                router,
            )

            self.assertFalse(diff["ok"])
            self.assertEqual(
                diff["error"]["code"],
                "DESKTOP_TASK_WORKTREE_UNAVAILABLE",
            )

    def test_automated_review_fails_closed_before_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            router = ExecutionRouter([FakeEngine()], default_engine="native")
            handle_request(
                {
                    "command": "task.create",
                    "task_id": "DIV-4",
                    "title": "Review me",
                },
                router,
            )

            review = handle_request(
                {"command": "task.review.auto", "task_id": "DIV-4"},
                router,
            )

            self.assertFalse(review["ok"])
            self.assertEqual(review["error"]["code"], "DESKTOP_VALIDATION_FAILED")
            self.assertIn("running", review["error"]["message"])

    def test_task_create_validates_title(self):
        response = handle_request({"command": "task.create", "title": "  "})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DESKTOP_TASK_TITLE_REQUIRED")

    def test_unknown_command_has_stable_error_code(self):
        response = handle_request({"command": "nope"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DESKTOP_COMMAND_UNKNOWN")

    def test_bridge_reads_and_writes_one_json_line(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ)
            env["DIVAN_DATA_DIR"] = directory
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "divan-desktop-bridge.py")],
                cwd=ROOT,
                env=env,
                input=json.dumps({"command": "capabilities"}) + "\n",
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["product"], "Divan")

    def test_bridge_rejects_invalid_json(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "divan-desktop-bridge.py")],
            cwd=ROOT,
            input="{\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["error"]["code"], "DESKTOP_REQUEST_INVALID_JSON")


if __name__ == "__main__":
    unittest.main()
