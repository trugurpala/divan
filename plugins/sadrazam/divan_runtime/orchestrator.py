from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import ordu
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
        planned = task.transition(TaskState.PLANNED, reason)
        work_plan = ordu.plan(planned.title)
        metadata = dict(planned.metadata)
        metadata["ordu"] = {
            "plan": work_plan,
            "unit_statuses": ordu.initial_unit_statuses(work_plan),
        }
        planned = replace(planned, metadata=metadata)
        for unit in work_plan["units"]:
            assert isinstance(unit, Mapping)
            unit_id = str(unit["id"])
            self.evidence.append(
                build_evidence(
                    planned.task_id,
                    "ordu-unit",
                    metadata["ordu"]["unit_statuses"][unit_id],
                    f"Ordu unit {unit_id} planned",
                    {
                        "unit_id": unit_id,
                        "role": str(unit["role"]),
                        "depends_on": list(unit["depends_on"]),
                        "phase": "planning",
                        "mutated": False,
                    },
                )
            )
        return self._save(planned)

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
        unit_status = "pass" if receipt.ok else "retry"
        running = self._set_ordu_unit_status(running, "implement", unit_status)
        self._record_ordu_unit(
            running,
            "implement",
            unit_status,
            phase="execution",
            data={
                "engine": receipt.engine,
                "exit_code": receipt.exit_code,
                "attempt": running.metadata.get("execution", {}).get("attempt"),
                "mandate_id": receipt.mandate_id,
            },
        )
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
        updated, decision = self.review(prepared, checks)
        unit_status = "pass" if decision.verdict is GateVerdict.PASS else "retry"
        updated = self._set_ordu_unit_status(updated, "verify", unit_status)
        updated = self._set_ordu_unit_status(updated, "review", unit_status)
        self._record_ordu_unit(
            updated,
            "verify",
            unit_status,
            phase="verification",
            data={"diff_sha256": snapshot.diff_sha256},
        )
        self._record_ordu_unit(
            updated,
            "review",
            unit_status,
            phase="review",
            data={"reviewer": automated.reviewer, "verdict": automated.verdict},
        )
        return self._save(updated), decision

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

    def _set_ordu_unit_status(
        self,
        task: DivanTask,
        unit_id: str,
        status: str,
    ) -> DivanTask:
        metadata = dict(task.metadata)
        ordu_data = metadata.get("ordu")
        if not isinstance(ordu_data, Mapping):
            return task
        statuses = ordu_data.get("unit_statuses")
        if not isinstance(statuses, Mapping) or unit_id not in statuses:
            return task
        next_ordu = dict(ordu_data)
        next_statuses = dict(statuses)
        next_statuses[unit_id] = status
        next_ordu["unit_statuses"] = next_statuses
        metadata["ordu"] = next_ordu
        return replace(task, metadata=metadata)

    def _record_ordu_unit(
        self,
        task: DivanTask,
        unit_id: str,
        status: str,
        *,
        phase: str,
        data: Mapping[str, Any],
    ) -> None:
        ordu_data = task.metadata.get("ordu")
        if not isinstance(ordu_data, Mapping):
            return
        plan_value = ordu_data.get("plan")
        if not isinstance(plan_value, Mapping):
            return
        units = plan_value.get("units")
        if not isinstance(units, list):
            return
        unit = next(
            (item for item in units if isinstance(item, Mapping) and item.get("id") == unit_id),
            None,
        )
        if unit is None:
            return
        self.evidence.append(
            build_evidence(
                task.task_id,
                "ordu-unit",
                status,
                f"Ordu unit {unit_id} {status}",
                {
                    "unit_id": unit_id,
                    "role": str(unit["role"]),
                    "depends_on": list(unit["depends_on"]),
                    "phase": phase,
                    **dict(data),
                },
            )
        )


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
