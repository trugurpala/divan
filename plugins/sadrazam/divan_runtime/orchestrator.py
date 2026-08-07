from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Mapping, Any

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

    def start(self, task: DivanTask, *, worktree_name: str, agent: str | None = None, prompt: str | None = None) -> DivanTask:
        running = task.transition(TaskState.RUNNING, "execution started")
        self.tasks.save(running)
        request = ExecutionRequest(
            action=ExecutionAction.WORKTREE_CREATE,
            project_root=running.project_root,
            mandate_id=running.mandate_id,
            args={"name": worktree_name, "agent": agent, "prompt": prompt},
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
                },
            )
        )
        if receipt.ok:
            return running
        return self._save(running.transition(TaskState.RETRY, "execution engine returned failure"))

    def review(self, task: DivanTask, checks: Iterable[CheckResult]) -> tuple[DivanTask, ReviewDecision]:
        reviewing = task if task.state is TaskState.REVIEW else task.transition(TaskState.REVIEW, "review started")
        decision = decide_review(checks)
        self.evidence.append(
            build_evidence(
                reviewing.task_id,
                "review",
                decision.verdict.value,
                "review gate decision",
                {
                    "verdict": decision.verdict.value,
                    "checks": [asdict(check) for check in decision.checks],
                    "reasons": list(decision.reasons),
                },
            )
        )
        target = TaskState.PASSED if decision.verdict is GateVerdict.PASS else TaskState.RETRY
        updated = reviewing.transition(target, "; ".join(decision.reasons) or None)
        return self._save(updated), decision

    def request_approval(self, task: DivanTask) -> DivanTask:
        return self._save(task.transition(TaskState.APPROVAL, "operator approval requested"))

    def approve_merge(self, task: DivanTask, review: ReviewDecision, *, approved: bool) -> DivanTask:
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
        return self._save(task.transition(TaskState.RELEASED, "release completed"))

    def _save(self, task: DivanTask) -> DivanTask:
        self.tasks.save(task)
        return task
