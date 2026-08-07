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
    engine_id = "native"

    def execute(self, request):
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=True,
            exit_code=0,
            payload={"worktree": "C:/worktree", "agent": "codex"},
            stdout="",
            stderr="",
            argv=("codex", "exec", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class OrchestratorTests(unittest.TestCase):
    def test_happy_path_survives_persisted_review_and_reaches_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            router = ExecutionRouter([FakeEngine()], default_engine="native")
            orchestrator = DivanOrchestrator(
                router,
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-1",
                title="Fix login",
                engine_id="native",
                mandate_id="m-1",
            )
            task = orchestrator.plan(task)
            task = orchestrator.start(
                task,
                worktree_name="fix-login",
                agent="codex",
                prompt="secret",
            )
            self.assertEqual(task.state, TaskState.RUNNING)
            self.assertEqual(task.metadata["execution"]["engine"], "native")

            task, decision = orchestrator.review(
                task,
                [CheckResult("tests", True), CheckResult("reviewer", True)],
            )
            self.assertEqual(task.state, TaskState.PASSED)
            self.assertEqual(task.metadata["review"]["verdict"], "pass")
            self.assertEqual(decision.verdict.value, "pass")

            task = orchestrator.tasks.load("DIV-1")
            task = orchestrator.request_approval(task)
            task = orchestrator.approve_merge(task, approved=True)
            self.assertEqual(task.state, TaskState.MERGED)
            task = orchestrator.release(task)
            self.assertEqual(task.state, TaskState.RELEASED)

            evidence = orchestrator.evidence.list("DIV-1")
            self.assertEqual(
                [item["kind"] for item in evidence],
                ["execution", "review", "approval", "release"],
            )
            self.assertNotIn("secret", str(evidence))

    def test_approval_requires_persisted_pass_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            orchestrator = DivanOrchestrator(
                ExecutionRouter([FakeEngine()], default_engine="native"),
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-2",
                title="No review",
                engine_id="native",
                mandate_id="m-2",
            )
            task = orchestrator.plan(task)
            task = task.transition(TaskState.RUNNING)
            task = task.transition(TaskState.REVIEW)
            task = task.transition(TaskState.PASSED)
            task = orchestrator.request_approval(task)
            with self.assertRaises(ValueError):
                orchestrator.approve_merge(task, approved=True)


if __name__ == "__main__":
    unittest.main()
