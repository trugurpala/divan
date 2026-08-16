from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_api import DesktopApi
from divan_runtime.desktop_protocol import handle_request
from divan_runtime.desktop_state import task_root
from divan_runtime.execution_contract import ExecutionAction, ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.project_readiness import ProjectReadiness, ToolStatus
from divan_runtime.task_model import DivanTask, TaskState
from divan_runtime.task_store import TaskStore


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


def _agent_readiness(
    agent: str = "codex", *, available: bool = True, auth: str = "connected"
) -> ProjectReadiness:
    return ProjectReadiness(
        ready=True,
        tools=(
            ToolStatus("git", True, "C:/git.exe", True),
            ToolStatus(
                agent,
                available,
                f"C:/{agent}.exe" if available else None,
                False,
                auth=auth,
            ),
        ),
    )


class DesktopProtocolTests(unittest.TestCase):
    def test_capabilities_response_has_envelope(self):
        response = handle_request(
            {"command": "capabilities"},
            ExecutionRouter([FakeEngine()]),
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["api_version"], 1)
        self.assertEqual(response["result"]["product"], "Ottoman")
        self.assertIn("task.start", response["result"]["commands"])
        self.assertIn("task.recover.interrupted", response["result"]["commands"])
        self.assertIn("task.diff", response["result"]["commands"])
        self.assertIn("task.review.auto", response["result"]["commands"])
        self.assertIn("interrupted-recovery", response["result"]["features"])

    @patch("divan_runtime.desktop_protocol_extensions.local_ai.status")
    def test_local_ai_status_is_available_without_an_execution_router(self, status):
        status.return_value = {"available": True, "models": []}
        response = handle_request({"command": "local_ai.status"})
        self.assertTrue(response["ok"])
        self.assertTrue(response["result"]["available"])

    @patch("divan_runtime.desktop_protocol_extensions.local_ai.draft")
    def test_local_ai_draft_stays_nonexecuting_without_an_execution_router(self, draft):
        draft.return_value = {
            "model": "qwen3:8b",
            "draft": "Önce incele, sonra doğrula.",
            "executed": False,
        }
        response = handle_request(
            {"command": "local_ai.draft", "prompt": "Ayar ekranını geliştir"}
        )
        self.assertTrue(response["ok"], response)
        self.assertFalse(response["result"]["executed"])
        draft.assert_called_once_with("Ayar ekranını geliştir", model="qwen3:8b")

    def test_ordu_plan_is_read_only_and_bounded(self):
        response = handle_request({"command": "ordu.plan", "title": "Build a settings panel"})
        self.assertTrue(response["ok"])
        self.assertTrue(response["result"]["approval_required_before_mutation"])

    @patch("divan_runtime.desktop_protocol.discover_tools")
    def test_task_create_plan_start_uses_explicit_approval(self, discover_tools):
        discover_tools.return_value = _agent_readiness()
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
            self.assertNotIn("execution_pending", started["result"]["metadata"])
            execution_evidence = next(
                item for item in evidence["result"] if item["kind"] == "execution"
            )
            self.assertNotIn("Fix login", str(execution_evidence["data"]["argv"]))

    @patch("divan_runtime.desktop_protocol.discover_tools")
    def test_interrupted_task_requires_explicit_recovery_then_fresh_execution_approval(self, discover_tools):
        discover_tools.return_value = _agent_readiness()
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            engine = FakeEngine()
            router = ExecutionRouter([engine], default_engine="native")
            handle_request(
                {"command": "task.create", "task_id": "DIV-REC", "title": "Recover me"},
                router,
            )
            handle_request({"command": "task.plan", "task_id": "DIV-REC"}, router)
            store = TaskStore(task_root())
            planned = store.load("DIV-REC")
            interrupted = replace(
                planned.transition(TaskState.RUNNING, "execution attempt 1 started"),
                engine_id="native",
                mandate_id="mandate-recovery",
                metadata={
                    "execution_pending": {
                        "attempt": 1,
                        "worktree_name": "DIV-REC",
                        "agent": "codex",
                    }
                },
            )
            store.save(interrupted)

            recovered = handle_request(
                {"command": "task.recover.interrupted", "task_id": "DIV-REC"},
                router,
            )
            self.assertTrue(recovered["ok"], recovered)
            self.assertEqual(recovered["result"]["state"], "retry")
            self.assertTrue(recovered["result"]["metadata"]["execution"]["interrupted"])
            self.assertEqual(engine.requests, [])

            denied = handle_request(
                {"command": "task.start", "task_id": "DIV-REC", "agent": "codex"},
                router,
            )
            self.assertFalse(denied["ok"])
            self.assertEqual(
                denied["error"]["code"],
                "DESKTOP_EXECUTION_APPROVAL_REQUIRED",
            )
            self.assertEqual(engine.requests, [])

            restarted = handle_request(
                {
                    "command": "task.start",
                    "task_id": "DIV-REC",
                    "agent": "codex",
                    "approve_execution": True,
                },
                router,
            )
            self.assertTrue(restarted["ok"], restarted)
            self.assertEqual(
                engine.requests[-1].args["name"],
                "DIV-REC-attempt-2",
            )
            recovery_evidence = handle_request(
                {"command": "evidence.list", "task_id": "DIV-REC"},
                router,
            )
            recovery = next(
                item for item in recovery_evidence["result"] if item["kind"] == "recovery"
            )
            self.assertFalse(recovery["data"]["resumed"])

    @patch("divan_runtime.desktop_protocol.discover_tools")
    def test_task_diff_uses_execution_worktree_without_mutation(self, discover_tools):
        discover_tools.return_value = _agent_readiness()
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
                "review_snapshot": {
                    "worktree": "C:/tmp/worktree",
                    "diff_sha256": "a" * 64,
                },
            },
        )

        diff = DesktopApi(router).task_diff(task)

        self.assertTrue(diff["staged"])
        self.assertEqual(diff["basis"], "review-snapshot")
        self.assertTrue(engine.requests[-1].args["staged"])

    def test_task_diff_does_not_reuse_stale_snapshot_after_retry_worktree_changes(self):
        engine = FakeEngine()
        router = ExecutionRouter([engine], default_engine="native")
        task = DivanTask(
            task_id="DIV-RETRY",
            title="Retried change",
            engine_id="native",
            mandate_id="mandate-retry",
            metadata={
                "execution": {"payload": {"worktree": "C:/tmp/new-worktree"}},
                "review_snapshot": {
                    "worktree": "C:/tmp/old-worktree",
                    "diff_sha256": "a" * 64,
                },
            },
        )

        diff = DesktopApi(router).task_diff(task)

        self.assertFalse(diff["staged"])
        self.assertEqual(diff["basis"], "working-tree")
        self.assertFalse(engine.requests[-1].args["staged"])
        self.assertEqual(engine.requests[-1].args["worktree"], "C:/tmp/new-worktree")

    @patch("divan_runtime.desktop_protocol.discover_tools")
    def test_task_start_rejects_unready_agent_before_creating_an_execution_attempt(
        self, discover_tools
    ):
        discover_tools.return_value = _agent_readiness(available=False, auth="unavailable")
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            engine = FakeEngine()
            router = ExecutionRouter([engine], default_engine="native")
            handle_request(
                {"command": "task.create", "task_id": "DIV-PREFLIGHT", "title": "Preflight me"},
                router,
            )
            handle_request({"command": "task.plan", "task_id": "DIV-PREFLIGHT"}, router)

            rejected = handle_request(
                {
                    "command": "task.start",
                    "task_id": "DIV-PREFLIGHT",
                    "agent": "codex",
                    "approve_execution": True,
                },
                router,
            )

            self.assertFalse(rejected["ok"])
            self.assertEqual(rejected["error"]["code"], "DESKTOP_AGENT_UNAVAILABLE")
            self.assertEqual(engine.requests, [])
            persisted = TaskStore(task_root()).load("DIV-PREFLIGHT")
            self.assertEqual(persisted.state, TaskState.PLANNED)
            self.assertIsNone(persisted.mandate_id)

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

    def test_prompt_search_and_task_creation_preserve_the_selected_prompt(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"DIVAN_DATA_DIR": directory}, clear=False
        ):
            found = handle_request({"command": "prompt.search", "query": "linux terminal"})
            self.assertTrue(found["ok"], found)
            self.assertTrue(found["result"]["items"])
            self.assertEqual(found["result"]["source"]["license"], "CC0-1.0")
            prompt_id = found["result"]["items"][0]["id"]
            created = handle_request(
                {"command": "task.create_from_prompt", "prompt_id": prompt_id},
                ExecutionRouter([FakeEngine()], default_engine="native"),
            )
            self.assertTrue(created["ok"], created)
            self.assertEqual(created["result"]["state"], "draft")
            source = created["result"]["metadata"]["prompt_library"]["source"]
            self.assertEqual(source["repository"], "https://github.com/f/prompts.chat")

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
        self.assertEqual(payload["result"]["product"], "Ottoman")

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
