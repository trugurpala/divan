from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_api import DesktopApi
from divan_runtime.execution_contract import ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.task_model import DivanTask


class FakeEngine:
    engine_id = "orca"

    def execute(self, request):
        return ExecutionReceipt("orca", request.action, True, 0, {"ready": True}, "", "", (), request.mandate_id)


class DesktopApiTests(unittest.TestCase):
    def test_capabilities_is_stable_json_shape(self):
        api = DesktopApi(ExecutionRouter([FakeEngine()]))
        value = api.capabilities()
        self.assertEqual(value["product"], "Ottoman")
        self.assertEqual(value["api_version"], 1)
        self.assertEqual(value["engines"], ("orca",))
        self.assertIn("approval-gate", value["features"])

    def test_engine_status_uses_router(self):
        api = DesktopApi(ExecutionRouter([FakeEngine()]))
        self.assertEqual(
            api.engine_status(),
            {"engine": "orca", "ok": True, "exit_code": 0, "payload": {"ready": True}},
        )

    def test_task_serialization(self):
        value = DesktopApi.serialize_tasks([DivanTask("task-1", "Fix login")])
        self.assertEqual(value[0]["task_id"], "task-1")
        self.assertEqual(value[0]["state"], "draft")


if __name__ == "__main__":
    unittest.main()
