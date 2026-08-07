from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .evidence import EvidenceStore, build_evidence
from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_router import ExecutionRouter
from .review_gate import CheckResult, GateVerdict, ReviewDecision, decide_review, require_release_ready
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
    ) -> None:
        self.router = router
        self.tasks = TaskStore(state_root)
        self.evidence = EvidenceStore(evidence_root)

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
        running = task.transition(TaskState.RUNNING, "execution started")
        self.tasks.save(running)
        request = ExecutionRequest(
            action=ExecutionAction.WORKTREE_CREATE,
            project_root=running.project_root,
            mandate_id=running.mandate_id,
            args={
                "name": worktree_name,
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
                },
            )
        )
        metadata = dict(running.metadata)
        metadata["execution"] = {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "payload": receipt.payload,
        }
        running = replace(running, engine_id=receipt.engine, metadata=metadata)
        self.tasks.save(running)
        if receipt.ok:
            return running
        return self._save(running.transition(TaskState.RETRY, "execution engine returned failure"))

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
        target = TaskState.PASSED if decision.verdict is GateVerdict.PASS else TaskState.RETRY
        updated = reviewing.transition(target, "; ".join(decision.reasons) or None)
        return self._save(updated), decision

    def request_approval(self, task: DivanTask) -> DivanTask:
        return self._save(task.transition(TaskState.APPROVAL, "operator approval requested"))

    def approve_merge(self, task: DivanTask, *, approved: bool) -> DivanTask:
        review = _review_from_task(task)
        require_release_ready(review=review, approved=approved, mandate_id=task.mandate_id)
        if task.state is not TaskState.APPROVAL:
            raise ValueError("task must be in approval state")
        self.evidence.append(
            build_evidence(
                task.task_id,
                "approval",
                "pass",
                "operator approved merge",
                {"mandate_id": task.mandate_id, "approved": True},
            )
        )
        return self._save(task.transition(TaskState.MERGED, "operator approved merge"))

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
    reasons = tuple(str(item) for item in reasons_raw) if isinstance(reasons_raw, list) else ()
    return ReviewDecision(GateVerdict(verdict_raw), tuple(checks), reasons)
