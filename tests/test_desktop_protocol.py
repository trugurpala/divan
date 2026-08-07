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

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.execution_contract import ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter


class FakeEngine:
    engine_id = "native"

    def execute(self, request):
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=True,
            exit_code=0,
            payload={"worktree": "C:/tmp/worktree", "agent": request.args.get("agent") or "codex"},
            stdout="",
            stderr="",
            argv=("codex", "exec", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class DesktopProtocolTests(unittest.TestCase):
    def test_capabilities_response_has_envelope(self):
        response = handle_request({"command": "capabilities"}, ExecutionRouter([FakeEngine()]))
        self.assertTrue(response["ok"])
        self.assertEqual(response["api_version"], 1)
        self.assertEqual(response["result"]["product"], "Divan")
        self.assertIn("task.start", response["result"]["commands"])

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
