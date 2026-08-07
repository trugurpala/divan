from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.orchestrator import DivanOrchestrator
from divan_runtime.reviewer_runner import AutomatedReview
from divan_runtime.task_model import TaskState


class FakeEngine:
    engine_id = "native"

    def __init__(self, worktree: str = "C:/worktree") -> None:
        self.worktree = worktree

    def execute(self, request):
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=True,
            exit_code=0,
            payload={"worktree": self.worktree, "agent": "codex"},
            stdout="",
            stderr="",
            argv=("codex", "exec", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class FlakyEngine:
    engine_id = "native"

    def __init__(self) -> None:
        self.names: list[str] = []

    def execute(self, request):
        name = str(request.args.get("name"))
        self.names.append(name)
        ok = len(self.names) > 1
        return ExecutionReceipt(
            engine="native",
            action=request.action,
            ok=ok,
            exit_code=0 if ok else 1,
            payload={"worktree": f"C:/worktrees/{name}", "agent": "codex"},
            stdout="",
            stderr="" if ok else "worker failed",
            argv=("codex", "exec", "<redacted-prompt>"),
            mandate_id=request.mandate_id,
        )


class FakeReviewer:
    def review(self, *, task_title: str, diff: str, worker_agent: str | None = None):
        self.last_task_title = task_title
        self.last_diff = diff
        self.last_worker_agent = worker_agent
        return AutomatedReview(
            reviewer="claude",
            verdict="PASS",
            summary="Patch is safe.",
            findings=(),
        )


def _git(directory: pathlib.Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(directory), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


class OrchestratorTests(unittest.TestCase):
    def test_happy_path_survives_persisted_review_and_reaches_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            project = root / "project"
            project.mkdir()
            _git(project, "init")
            _git(project, "config", "user.name", "Divan Test")
            _git(project, "config", "user.email", "divan-test@example.invalid")
            (project / "app.txt").write_text("before\n", encoding="utf-8")
            _git(project, "add", "app.txt")
            _git(project, "commit", "-m", "initial")

            worktree = root / "worker"
            _git(
                project,
                "worktree",
                "add",
                "-b",
                "divan-test-worker",
                str(worktree),
                "HEAD",
            )
            (worktree / "app.txt").write_text("after\n", encoding="utf-8")

            reviewer = FakeReviewer()
            router = ExecutionRouter(
                [FakeEngine(str(worktree))],
                default_engine="native",
            )
            orchestrator = DivanOrchestrator(
                router,
                state_root=root / "tasks",
                evidence_root=root / "evidence",
                reviewer=reviewer,
            )
            task = orchestrator.create_task(
                task_id="DIV-1",
                title="Fix login",
                project_root=str(project),
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
            self.assertEqual(task.metadata["execution"]["attempt"], 1)
            self.assertNotIn("execution_pending", task.metadata)

            task, decision = orchestrator.review_automated(task)
            self.assertEqual(task.state, TaskState.PASSED)
            self.assertEqual(task.metadata["review"]["verdict"], "pass")
            self.assertEqual(task.metadata["automated_review"]["reviewer"], "claude")
            self.assertEqual(decision.verdict.value, "pass")
            self.assertEqual(reviewer.last_worker_agent, "codex")
            self.assertIn("app.txt", reviewer.last_diff)

            task = orchestrator.tasks.load("DIV-1")
            task = orchestrator.request_approval(task)
            task = orchestrator.approve_merge(task, approved=True)
            self.assertEqual(task.state, TaskState.MERGED)
            self.assertEqual(
                (project / "app.txt").read_text(encoding="utf-8"),
                "after\n",
            )
            self.assertEqual(
                _git(project, "rev-parse", "HEAD"),
                task.metadata["merge"]["commit_sha"],
            )

            task = orchestrator.release(task)
            self.assertEqual(task.state, TaskState.RELEASED)

            evidence = orchestrator.evidence.list("DIV-1")
            self.assertEqual(
                [item["kind"] for item in evidence],
                ["execution", "review", "approval", "release"],
            )
            self.assertNotIn("secret", str(evidence))

    def test_retry_uses_fresh_worktree_name_and_preserves_attempt_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            engine = FlakyEngine()
            orchestrator = DivanOrchestrator(
                ExecutionRouter([engine], default_engine="native"),
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-RETRY",
                title="Retry worker",
                engine_id="native",
                mandate_id="m-retry",
            )
            task = orchestrator.plan(task)
            task = orchestrator.start(
                task,
                worktree_name="DIV-RETRY",
                agent="codex",
            )
            self.assertEqual(task.state, TaskState.RETRY)

            task = orchestrator.start(
                task,
                worktree_name="DIV-RETRY",
                agent="codex",
            )
            self.assertEqual(task.state, TaskState.RUNNING)
            self.assertEqual(engine.names, ["DIV-RETRY", "DIV-RETRY-attempt-2"])
            self.assertEqual(task.metadata["execution"]["attempt"], 2)
            self.assertEqual(
                [row["attempt"] for row in task.metadata["execution_history"]],
                [1, 2],
            )

    def test_restart_recovery_marks_interrupted_attempt_retry_without_resuming_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            engine = FlakyEngine()
            router = ExecutionRouter([engine], default_engine="native")
            orchestrator = DivanOrchestrator(
                router,
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-RECOVER",
                title="Recover interrupted worker",
                engine_id="native",
                mandate_id="m-recover",
            )
            task = orchestrator.plan(task)
            interrupted = replace(
                task.transition(TaskState.RUNNING, "execution attempt 1 started"),
                metadata={
                    "execution_pending": {
                        "attempt": 1,
                        "worktree_name": "DIV-RECOVER",
                        "agent": "codex",
                    }
                },
            )
            orchestrator.tasks.save(interrupted)

            restarted = DivanOrchestrator(
                router,
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            recovered = restarted.recover_interrupted(
                restarted.tasks.load("DIV-RECOVER")
            )

            self.assertEqual(engine.names, [])
            self.assertEqual(recovered.state, TaskState.RETRY)
            self.assertTrue(recovered.metadata["execution"]["interrupted"])
            self.assertEqual(recovered.metadata["execution"]["attempt"], 1)
            self.assertNotIn("execution_pending", recovered.metadata)
            recovery_evidence = restarted.evidence.list("DIV-RECOVER")
            self.assertEqual(recovery_evidence[-1]["kind"], "recovery")
            self.assertFalse(recovery_evidence[-1]["data"]["resumed"])

            retried = restarted.start(
                recovered,
                worktree_name="DIV-RECOVER",
                agent="codex",
            )
            self.assertEqual(engine.names, ["DIV-RECOVER-attempt-2"])
            self.assertEqual(retried.metadata["execution"]["attempt"], 2)

    def test_recovery_rejects_completed_execution_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            orchestrator = DivanOrchestrator(
                ExecutionRouter([FakeEngine()], default_engine="native"),
                state_root=root / "tasks",
                evidence_root=root / "evidence",
            )
            task = orchestrator.create_task(
                task_id="DIV-COMPLETE",
                title="Completed worker",
                engine_id="native",
                mandate_id="m-complete",
            )
            task = orchestrator.plan(task)
            task = orchestrator.start(task, worktree_name="DIV-COMPLETE", agent="codex")
            with self.assertRaisesRegex(ValueError, "execution receipt"):
                orchestrator.recover_interrupted(task)

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
