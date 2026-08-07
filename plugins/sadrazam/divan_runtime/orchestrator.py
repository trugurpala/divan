from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .evidence import EvidenceStore, build_evidence
from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_router import ExecutionRouter
from .git_guard import (
    GitRunner,
    commit_and_fast_forward,
    snapshot_from_metadata,
    stage_review_snapshot,
)
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
    ) -> None:
        self.router = router
        self.tasks = TaskStore(state_root)
        self.evidence = EvidenceStore(evidence_root)
        self.reviewer = reviewer or AutomatedReviewer()
        self.git_runner = git_runner

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
        attempt = _next_execution_attempt(task)
        execution_name = (
            worktree_name
            if attempt == 1
            else f"{worktree_name}-attempt-{attempt}"
        )
        pending_metadata = dict(task.metadata)
        # A new attempt must never expose the previous attempt as the active receipt.
        # execution_history retains prior evidence; active execution/review state is reset
        # before the engine is invoked so a crash can be recovered unambiguously.
        pending_metadata.pop("execution", None)
        pending_metadata.pop("review_snapshot", None)
        pending_metadata.pop("automated_review", None)
        pending_metadata.pop("review", None)
        pending_metadata["execution_pending"] = {
            "attempt": attempt,
            "worktree_name": execution_name,
            "agent": agent,
        }
        running = replace(
            task.transition(TaskState.RUNNING, f"execution attempt {attempt} started"),
            metadata=pending_metadata,
        )
        self.tasks.save(running)
        request = ExecutionRequest(
            action=ExecutionAction.WORKTREE_CREATE,
            project_root=running.project_root,
            mandate_id=running.mandate_id,
            args={
                "name": execution_name,
                "agent": agent,
                "prompt": prompt or running.title,
            },
        )
        receipt = self.router.execute(request, running.engine_id)
        self.evidence.append(
            build_evidence(
                running.task_id,
                "execution",
                "pass" if receipt.ok else "fail",
                f"{receipt.engine} {receipt.action.value}",
                {
                    "engine": receipt.engine,
                    "action": receipt.action.value,
                    "exit_code": receipt.exit_code,
                    "argv": list(receipt.argv),
                    "mandate_id": receipt.mandate_id,
                    "payload": receipt.payload,
                    "attempt": attempt,
                    "worktree_name": execution_name,
                },
            )
        )
        execution_record = {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "payload": receipt.payload,
            "attempt": attempt,
            "worktree_name": execution_name,
        }
        metadata = dict(running.metadata)
        metadata.pop("execution_pending", None)
        metadata["execution"] = execution_record
        history_raw = metadata.get("execution_history")
        history = list(history_raw) if isinstance(history_raw, list) else []
        history.append(execution_record)
        metadata["execution_history"] = history
        running = replace(running, engine_id=receipt.engine, metadata=metadata)
        self.tasks.save(running)
        if receipt.ok:
            return running
        return self._save(
            running.transition(TaskState.RETRY, "execution engine returned failure")
        )

    def recover_interrupted(self, task: DivanTask) -> DivanTask:
        """Move a persisted interrupted RUNNING task to RETRY without resuming mutation."""
        if task.state is not TaskState.RUNNING:
            raise ValueError("only a running task can be recovered as interrupted")
        if isinstance(task.metadata.get("execution"), Mapping):
            raise ValueError(
                "task already has an execution receipt; review it instead of recovering it"
            )

        metadata = dict(task.metadata)
        pending = metadata.get("execution_pending")
        pending_map = pending if isinstance(pending, Mapping) else {}
        raw_attempt = pending_map.get("attempt")
        attempt = (
            raw_attempt
            if isinstance(raw_attempt, int)
            and not isinstance(raw_attempt, bool)
            and raw_attempt >= 1
            else 1
        )
        worktree_name = pending_map.get("worktree_name")
        if not isinstance(worktree_name, str) or not worktree_name.strip():
            worktree_name = task.task_id
        agent = pending_map.get("agent")
        if not isinstance(agent, str) or not agent.strip():
            agent = None

        interrupted_record = {
            "engine": task.engine_id or "unknown",
            "ok": False,
            "exit_code": None,
            "payload": {},
            "attempt": attempt,
            "worktree_name": worktree_name,
            "agent": agent,
            "interrupted": True,
        }
        metadata.pop("execution_pending", None)
        metadata["execution"] = interrupted_record
        history_raw = metadata.get("execution_history")
        history = list(history_raw) if isinstance(history_raw, list) else []
        history.append(interrupted_record)
        metadata["execution_history"] = history
        prepared = replace(task, metadata=metadata)
        recovered = prepared.transition(
            TaskState.RETRY,
            f"execution attempt {attempt} interrupted; explicit retry required",
        )
        self.evidence.append(
            build_evidence(
                task.task_id,
                "recovery",
                "retry",
                "interrupted execution recovered without resuming mutation",
                {
                    "engine": task.engine_id,
                    "attempt": attempt,
                    "worktree_name": worktree_name,
                    "mandate_id": task.mandate_id,
                    "resumed": False,
                },
            )
        )
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
        return self._save(
            approved_task.transition(TaskState.MERGED, "reviewed snapshot fast-forwarded")
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


def _next_execution_attempt(task: DivanTask) -> int:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        return 1
    attempt = execution.get("attempt")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt >= 1:
        return attempt + 1
    return 2


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
