from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.orchestrator import DivanOrchestrator
from divan_runtime.review_gate import CheckResult
from divan_runtime.task_model import TaskState


class FakeEngine:
    engine_id = "orca"

    def execute(self, request):
        return ExecutionReceipt(
            engine="orca",
            action=request.action,
            ok=True,
            exit_code=0,
            payload={"worktree": "fix-login"},
            stdout="",
            stderr="",
            argv=("orca", "worktree", "create", "--prompt", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class OrchestratorTests(unittest.TestCase):
    def test_happy_path_reaches_merged_with_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            orchestrator = DivanOrchestrator(
                ExecutionRouter([FakeEngine()]),
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-1",
                title="Fix login",
                engine_id="orca",
                mandate_id="m-1",
            )
            task = orchestrator.plan(task)
            task = orchestrator.start(task, worktree_name="fix-login", agent="codex", prompt="secret")
            self.assertEqual(task.state, TaskState.RUNNING)
            task, review = orchestrator.review(task, [CheckResult("tests", True), CheckResult("reviewer", True)])
            self.assertEqual(task.state, TaskState.PASSED)
            task = orchestrator.request_approval(task)
            task = orchestrator.approve_merge(task, review, approved=True)
            self.assertEqual(task.state, TaskState.MERGED)
            evidence = orchestrator.evidence.list("DIV-1")
            self.assertEqual([item["kind"] for item in evidence], ["execution", "review", "approval"])
            self.assertNotIn("secret", str(evidence))


if __name__ == "__main__":
    unittest.main()
