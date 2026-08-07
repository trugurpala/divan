from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionAction, ExecutionPolicyError, ExecutionReceipt, ExecutionRequest
from divan_runtime.execution_router import ExecutionRouter


class FakeEngine:
    def __init__(self, engine_id: str) -> None:
        self.engine_id = engine_id
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return ExecutionReceipt(self.engine_id, request.action, True, 0, {}, "", "", (), request.mandate_id)


class ExecutionRouterTests(unittest.TestCase):
    def test_single_engine_is_selected_automatically(self):
        engine = FakeEngine("orca")
        router = ExecutionRouter([engine])
        result = router.execute(ExecutionRequest(ExecutionAction.STATUS))
        self.assertEqual(result.engine, "orca")

    def test_multiple_engines_require_selection(self):
        router = ExecutionRouter([FakeEngine("orca"), FakeEngine("local")])
        with self.assertRaises(ExecutionPolicyError):
            router.execute(ExecutionRequest(ExecutionAction.STATUS))

    def test_mutating_request_requires_mandate_before_engine_call(self):
        engine = FakeEngine("orca")
        router = ExecutionRouter([engine])
        with self.assertRaises(ExecutionPolicyError):
            router.execute(ExecutionRequest(ExecutionAction.WORKTREE_CREATE))
        self.assertEqual(engine.requests, [])


if __name__ == "__main__":
    unittest.main()
