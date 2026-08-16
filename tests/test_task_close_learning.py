from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.execution_contract import ExecutionReceipt
from divan_runtime.execution_router import ExecutionRouter
from divan_runtime.knowledge_store import KnowledgeStore
from divan_runtime.orchestrator import DivanOrchestrator
from divan_runtime.review_gate import CheckResult
from divan_runtime.reviewer_runner import AutomatedReview
from divan_runtime.task_model import TaskState


class _Engine:
    engine_id = "native"

    def __init__(self, worktree: str) -> None:
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


class _PassingReviewer:
    def review(self, *, task_title: str, diff: str, worker_agent: str | None = None):
        return AutomatedReview(
            reviewer="claude", verdict="PASS", summary="Patch is safe.", findings=()
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


class TaskCloseLearningTests(unittest.TestCase):
    """A merged task that review once rejected must leave a lesson behind.

    This is the write half of the Agency Memory contract. Without it the
    knowledge store has no production writer and stays empty forever.
    """

    def _project(self, root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
        project = root / "project"
        project.mkdir()
        _git(project, "init")
        _git(project, "config", "user.name", "Divan Test")
        _git(project, "config", "user.email", "divan-test@example.invalid")
        (project / "app.txt").write_text("before\n", encoding="utf-8")
        _git(project, "add", "app.txt")
        _git(project, "commit", "-m", "initial")
        worktree = root / "worker"
        _git(project, "worktree", "add", "-b", "divan-test-worker", str(worktree), "HEAD")
        (worktree / "app.txt").write_text("after\n", encoding="utf-8")
        return project, worktree

    def _merge_after_failed_review(
        self, root: pathlib.Path, knowledge: KnowledgeStore
    ):
        project, worktree = self._project(root)
        orchestrator = DivanOrchestrator(
            ExecutionRouter([_Engine(str(worktree))], default_engine="native"),
            state_root=root / "tasks",
            evidence_root=root / "evidence",
            reviewer=_PassingReviewer(),
            knowledge=knowledge,
        )
        task = orchestrator.create_task(
            task_id="DIV-1",
            title="Fix login",
            project_root=str(project),
            engine_id="native",
            mandate_id="m-1",
        )
        task = orchestrator.plan(task)
        task = orchestrator.start(task, worktree_name="fix-login", agent="codex")

        # First review rejects the attempt.
        task, decision = orchestrator.review(
            task,
            [
                CheckResult(name="tests", passed=False, summary="2 failing tests"),
                CheckResult(name="lint", passed=True),
            ],
        )
        self.assertEqual(task.state, TaskState.RETRY)
        self.assertEqual(len(task.metadata["failed_reviews"]), 1)

        # The retried change then passes every gate and merges.
        task = orchestrator.start(task, worktree_name="fix-login", agent="codex")
        task, _ = orchestrator.review_automated(task)
        self.assertEqual(task.state, TaskState.PASSED)
        task = orchestrator.request_approval(orchestrator.tasks.load("DIV-1"))
        task = orchestrator.approve_merge(task, approved=True)
        self.assertEqual(task.state, TaskState.MERGED)
        return orchestrator, task

    def test_a_rejected_then_merged_task_writes_a_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            knowledge = KnowledgeStore(root / "knowledge.sqlite3")
            orchestrator, task = self._merge_after_failed_review(root, knowledge)

            lessons = knowledge.search("review")
            self.assertEqual(len(lessons), 1, lessons)
            lesson = lessons[0]
            self.assertIn("tests", lesson.tags)
            self.assertIn("Fix login", lesson.summary)
            self.assertEqual(
                lesson.evidence_sha256, task.metadata["merge"]["diff_sha256"]
            )
            # Provenance must be reconstructable from evidence, not just memory.
            captured = [
                item
                for item in orchestrator.evidence.list("DIV-1")
                if item.get("kind") == "knowledge"
            ]
            self.assertEqual(len(captured), 1, captured)
            self.assertEqual(captured[0]["status"], "pass")
            self.assertEqual(captured[0]["data"]["item_id"], lesson.item_id)

    def test_a_task_that_never_failed_review_teaches_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            knowledge = KnowledgeStore(root / "knowledge.sqlite3")
            project, worktree = self._project(root)
            orchestrator = DivanOrchestrator(
                ExecutionRouter([_Engine(str(worktree))], default_engine="native"),
                state_root=root / "tasks",
                evidence_root=root / "evidence",
                reviewer=_PassingReviewer(),
                knowledge=knowledge,
            )
            task = orchestrator.create_task(
                task_id="DIV-2",
                title="Clean pass",
                project_root=str(project),
                engine_id="native",
                mandate_id="m-2",
            )
            task = orchestrator.plan(task)
            task = orchestrator.start(task, worktree_name="clean", agent="codex")
            task, _ = orchestrator.review_automated(task)
            task = orchestrator.request_approval(orchestrator.tasks.load("DIV-2"))
            task = orchestrator.approve_merge(task, approved=True)

            self.assertEqual(task.state, TaskState.MERGED)
            self.assertEqual(knowledge.analytics()["items"], 0)

    def test_a_broken_knowledge_store_cannot_fail_a_merge(self) -> None:
        class _BrokenStore(KnowledgeStore):
            def upsert(self, item):  # type: ignore[override]
                raise RuntimeError("knowledge store unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            broken = _BrokenStore(root / "knowledge.sqlite3")
            orchestrator, task = self._merge_after_failed_review(root, broken)

            self.assertEqual(task.state, TaskState.MERGED)
            failures = [
                item
                for item in orchestrator.evidence.list("DIV-1")
                if item.get("kind") == "knowledge"
            ]
            self.assertEqual(len(failures), 1, failures)
            self.assertEqual(failures[0]["status"], "fail")


if __name__ == "__main__":
    unittest.main()
