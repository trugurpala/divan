from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .desktop_state import knowledge_database
from .evidence import EvidenceStore, build_evidence
from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_recovery import (
    complete_execution_attempt,
    execution_attempt_evidence,
    prepare_execution_attempt,
    recover_interrupted_attempt,
)
from .execution_router import ExecutionRouter
from .git_guard import (
    GitRunner,
    commit_and_fast_forward,
    snapshot_from_metadata,
    stage_review_snapshot,
)
from .knowledge_capture import lesson_from_failure
from .knowledge_store import KnowledgeStore
from .review_gate import (
    CheckResult,
    GateVerdict,
    ReviewDecision,
    decide_review,
    require_release_ready,
)
from .reviewer_runner import AutomatedReview, AutomatedReviewer, ReviewerUnavailable
from .task_model import DivanTask, TaskState
from .task_store import TaskStore


class DivanOrchestrator:
    """Coordinates task state, execution, evidence, review and approval.

    The orchestrator owns product workflow. Execution engines remain replaceable.
    """

    def __init__(
        self,
        router: ExecutionRouter,
        state_root: Path | str = ".divan/tasks",
        evidence_root: Path | str = ".divan/evidence",
        *,
        reviewer: AutomatedReviewer | None = None,
        git_runner: GitRunner | None = None,
        knowledge: KnowledgeStore | None = None,
    ) -> None:
        self.router = router
        self.tasks = TaskStore(state_root)
        self.evidence = EvidenceStore(evidence_root)
        self.reviewer = reviewer or AutomatedReviewer()
        self.git_runner = git_runner
        self.knowledge = knowledge or KnowledgeStore(knowledge_database())

    def create_task(
        self,
        *,
        task_id: str,
        title: str,
        project_root: str | None = None,
        engine_id: str | None = None,
        mandate_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> DivanTask:
        task = DivanTask(
            task_id=task_id,
            title=title,
            project_root=project_root,
            engine_id=engine_id,
            mandate_id=mandate_id,
            metadata=dict(metadata or {}),
        )
        self.tasks.save(task)
        return task

    def plan(self, task: DivanTask, reason: str | None = None) -> DivanTask:
        return self._save(task.transition(TaskState.PLANNED, reason))

    def start(
        self,
        task: DivanTask,
        *,
        worktree_name: str,
        agent: str | None = None,
        prompt: str | None = None,
    ) -> DivanTask:
        pending = prepare_execution_attempt(
            task,
            worktree_name=worktree_name,
            agent=agent,
        )
        self.tasks.save(pending.running)
        request = ExecutionRequest(
            action=ExecutionAction.WORKTREE_CREATE,
            project_root=pending.running.project_root,
            mandate_id=pending.running.mandate_id,
            args={
                "name": pending.worktree_name,
                "agent": agent,
                "prompt": prompt or pending.running.title,
            },
        )
        receipt = self.router.execute(request, pending.running.engine_id)
        self.evidence.append(execution_attempt_evidence(pending, receipt))
        running = complete_execution_attempt(pending, receipt)
        self.tasks.save(running)
        if receipt.ok:
            return running
        return self._save(
            running.transition(TaskState.RETRY, "execution engine returned failure")
        )

    def recover_interrupted(self, task: DivanTask) -> DivanTask:
        """Move a persisted interrupted RUNNING task to RETRY without resuming mutation."""
        recovered, evidence = recover_interrupted_attempt(task)
        self.evidence.append(evidence)
        return self._save(recovered)

    def review(
        self,
        task: DivanTask,
        checks: Iterable[CheckResult],
    ) -> tuple[DivanTask, ReviewDecision]:
        reviewing = (
            task
            if task.state is TaskState.REVIEW
            else task.transition(TaskState.REVIEW, "review started")
        )
        decision = decide_review(checks)
        serialized_checks = [asdict(check) for check in decision.checks]
        self.evidence.append(
            build_evidence(
                reviewing.task_id,
                "review",
                decision.verdict.value,
                "review gate decision",
                {
                    "verdict": decision.verdict.value,
                    "checks": serialized_checks,
                    "reasons": list(decision.reasons),
                },
            )
        )
        metadata = dict(reviewing.metadata)
        metadata["review"] = {
            "verdict": decision.verdict.value,
            "checks": serialized_checks,
            "reasons": list(decision.reasons),
        }
        if decision.verdict is not GateVerdict.PASS:
            # Remember why review rejected this attempt. On its own a rejection
            # is only half a lesson; the merge that finally lands supplies the
            # other half.
            metadata["failed_reviews"] = [
                *_failed_reviews(reviewing),
                {
                    "verdict": decision.verdict.value,
                    "reasons": list(decision.reasons),
                    "failed_checks": [
                        check["name"]
                        for check in serialized_checks
                        if check.get("passed") is not True
                    ],
                },
            ]
        reviewing = replace(reviewing, metadata=metadata)
        target = (
            TaskState.PASSED
            if decision.verdict is GateVerdict.PASS
            else TaskState.RETRY
        )
        updated = reviewing.transition(target, "; ".join(decision.reasons) or None)
        return self._save(updated), decision

    def review_automated(self, task: DivanTask) -> tuple[DivanTask, ReviewDecision]:
        if task.state not in {TaskState.RUNNING, TaskState.REVIEW}:
            raise ValueError("task must be running before automated review")
        if not task.project_root:
            raise ValueError("task requires project_root for automated review")
        worktree = _execution_worktree(task)
        snapshot = stage_review_snapshot(
            task.project_root,
            worktree,
            runner=self.git_runner,
        )
        worker_agent = _worker_agent(task)
        try:
            automated = self.reviewer.review(
                task_title=task.title,
                diff=snapshot.diff,
                worker_agent=worker_agent,
            )
        except ReviewerUnavailable as error:
            automated = AutomatedReview(
                reviewer="unavailable",
                verdict="RETRY",
                summary=str(error),
                findings=("independent reviewer unavailable",),
            )
        metadata = dict(task.metadata)
        metadata["review_snapshot"] = snapshot.metadata()
        metadata["automated_review"] = {
            "reviewer": automated.reviewer,
            "verdict": automated.verdict,
            "summary": automated.summary,
            "findings": list(automated.findings),
        }
        prepared = replace(task, metadata=metadata)
        self.tasks.save(prepared)
        execution_ok = _execution_ok(prepared)
        checks = (
            CheckResult(
                "execution",
                execution_ok,
                True,
                "worker execution failed" if not execution_ok else "worker execution passed",
            ),
            CheckResult(
                "review-snapshot",
                True,
                True,
                f"sha256:{snapshot.diff_sha256}",
            ),
            automated.check(),
        )
        return self.review(prepared, checks)

    def request_approval(self, task: DivanTask) -> DivanTask:
        return self._save(
            task.transition(TaskState.APPROVAL, "operator approval requested")
        )

    def approve_merge(self, task: DivanTask, *, approved: bool) -> DivanTask:
        review = _review_from_task(task)
        require_release_ready(
            review=review,
            approved=approved,
            mandate_id=task.mandate_id,
        )
        if task.state is not TaskState.APPROVAL:
            raise ValueError("task must be in approval state")
        _require_automated_pass(task)
        if not task.project_root:
            raise ValueError("task requires project_root for guarded merge")
        snapshot = snapshot_from_metadata(task.metadata.get("review_snapshot"))
        merged = commit_and_fast_forward(
            task.project_root,
            snapshot,
            message=f"divan: {task.title}",
            runner=self.git_runner,
        )
        metadata = dict(task.metadata)
        metadata["merge"] = {
            "commit_sha": merged.commit_sha,
            "base_head": merged.base_head,
            "diff_sha256": merged.diff_sha256,
        }
        approved_task = replace(task, metadata=metadata)
        self.evidence.append(
            build_evidence(
                task.task_id,
                "approval",
                "pass",
                "operator approved reviewed fast-forward merge",
                {
                    "mandate_id": task.mandate_id,
                    "approved": True,
                    "commit_sha": merged.commit_sha,
                    "base_head": merged.base_head,
                    "diff_sha256": merged.diff_sha256,
                },
            )
        )
        self._capture_merge_lesson(approved_task, merged.diff_sha256)
        return self._save(
            approved_task.transition(TaskState.MERGED, "reviewed snapshot fast-forwarded")
        )

    def _capture_merge_lesson(self, task: DivanTask, diff_sha256: str) -> None:
        """Record what review rejected and what finally landed, at task close.

        Only tasks that actually failed review carry a lesson: a task that
        passed first time teaches nothing worth storing. Memory capture is
        never allowed to fail a merge that already passed every gate, so a
        broken knowledge store degrades to an honest evidence entry.
        """
        failures = _failed_reviews(task)
        if not failures:
            return
        reasons = [
            reason
            for failure in failures
            for reason in failure.get("reasons", [])
            if isinstance(reason, str)
        ]
        checks = sorted(
            {
                name
                for failure in failures
                for name in failure.get("failed_checks", [])
                if isinstance(name, str)
            }
        )
        problem = (
            f"Review rejected {task.title} {len(failures)} time(s). "
            f"Failing checks: {', '.join(checks) or 'unnamed'}. "
            f"Reasons: {'; '.join(reasons) or 'not recorded'}"
        )
        solution = (
            f"The change that passed every required check merged as {diff_sha256}."
        )
        try:
            lesson = lesson_from_failure(
                problem=problem,
                solution=solution,
                tags=("review", *checks),
                source_project=task.project_root,
                evidence_sha256=diff_sha256,
            )
            self.knowledge.upsert(lesson)
        except Exception as error:  # noqa: BLE001 - memory must not fail a merge
            self.evidence.append(
                build_evidence(
                    task.task_id,
                    "knowledge",
                    "fail",
                    "task-close lesson capture failed",
                    {"error": type(error).__name__},
                )
            )
            return
        self.evidence.append(
            build_evidence(
                task.task_id,
                "knowledge",
                "pass",
                "task-close lesson captured",
                {
                    "item_id": lesson.item_id,
                    "failed_review_count": len(failures),
                    "failed_checks": checks,
                    "evidence_sha256": diff_sha256,
                },
            )
        )

    def release(self, task: DivanTask) -> DivanTask:
        if task.state is not TaskState.MERGED:
            raise ValueError("task must be merged before release")
        self.evidence.append(
            build_evidence(
                task.task_id,
                "release",
                "pass",
                "release completed",
                {"mandate_id": task.mandate_id},
            )
        )
        return self._save(task.transition(TaskState.RELEASED, "release completed"))

    def _save(self, task: DivanTask) -> DivanTask:
        self.tasks.save(task)
        return task


def _execution_worktree(task: DivanTask) -> str:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        raise ValueError("task has no execution receipt")
    payload = execution.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("task execution receipt has no payload")
    value = payload.get("worktree")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("task has no execution worktree")
    return value.strip()


def _worker_agent(task: DivanTask) -> str | None:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        return None
    payload = execution.get("payload")
    if not isinstance(payload, Mapping):
        return None
    value = payload.get("agent")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _execution_ok(task: DivanTask) -> bool:
    execution = task.metadata.get("execution")
    return isinstance(execution, Mapping) and execution.get("ok") is True


def _require_automated_pass(task: DivanTask) -> None:
    value = task.metadata.get("automated_review")
    if not isinstance(value, Mapping):
        raise ValueError("approval requires an independent automated review")
    reviewer = value.get("reviewer")
    verdict = value.get("verdict")
    if reviewer not in {"claude", "codex"} or verdict != "PASS":
        raise ValueError("approval requires PASS from Claude or Codex independent review")


def _review_from_task(task: DivanTask) -> ReviewDecision:
    value = task.metadata.get("review")
    if not isinstance(value, Mapping):
        raise ValueError("task has no persisted review decision")
    verdict_raw = value.get("verdict")
    checks_raw = value.get("checks")
    reasons_raw = value.get("reasons", [])
    if not isinstance(verdict_raw, str) or not isinstance(checks_raw, list):
        raise ValueError("persisted review decision is invalid")
    checks: list[CheckResult] = []
    for item in checks_raw:
        if not isinstance(item, Mapping):
            raise ValueError("persisted review check is invalid")
        checks.append(
            CheckResult(
                name=str(item.get("name", "")),
                passed=bool(item.get("passed")),
                required=bool(item.get("required", True)),
                summary=str(item.get("summary", "")),
            )
        )
    reasons = (
        tuple(str(item) for item in reasons_raw)
        if isinstance(reasons_raw, list)
        else ()
    )
    return ReviewDecision(GateVerdict(verdict_raw), tuple(checks), reasons)


def _failed_reviews(task: DivanTask) -> list[dict[str, Any]]:
    """Return the recorded review rejections for one task."""
    recorded = task.metadata.get("failed_reviews")
    if not isinstance(recorded, list):
        return []
    return [entry for entry in recorded if isinstance(entry, dict)]
