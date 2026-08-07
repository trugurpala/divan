from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .execution_contract import ExecutionAction, ExecutionRequest
from .execution_router import ExecutionRouter
from .task_model import DivanTask, TaskState


@dataclass(frozen=True)
class DesktopCapabilities:
    product: str
    api_version: int
    engines: tuple[str, ...]
    task_states: tuple[str, ...]
    features: tuple[str, ...]


class DesktopApi:
    """Stable facade between the desktop shell and Divan Core."""

    API_VERSION = 1

    def __init__(self, router: ExecutionRouter) -> None:
        self.router = router

    def capabilities(self) -> dict[str, Any]:
        value = DesktopCapabilities(
            product="Divan",
            api_version=self.API_VERSION,
            engines=self.router.available_engines(),
            task_states=tuple(state.value for state in TaskState),
            features=(
                "engine-routing",
                "mandate-gate",
                "task-lifecycle",
                "interrupted-recovery",
                "evidence",
                "approval-gate",
                "task-diff",
            ),
        )
        return asdict(value)

    def engine_status(self, engine_id: str | None = None) -> dict[str, Any]:
        receipt = self.router.execute(ExecutionRequest(ExecutionAction.STATUS), engine_id)
        return {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "payload": receipt.payload,
        }

    def task_diff(
        self,
        task: DivanTask,
        *,
        worktree: str | None = None,
        path: str = "*",
        staged: bool | None = None,
    ) -> dict[str, Any]:
        active_worktree = worktree or self.execution_worktree(task)
        if active_worktree is None:
            raise ValueError("task has no execution worktree yet")
        review_snapshot = task.metadata.get("review_snapshot")
        snapshot_worktree = (
            review_snapshot.get("worktree")
            if isinstance(review_snapshot, Mapping)
            else None
        )
        has_current_review_snapshot = bool(
            isinstance(snapshot_worktree, str)
            and snapshot_worktree.strip()
            and _same_worktree(snapshot_worktree, active_worktree)
        )
        use_staged = has_current_review_snapshot if staged is None else staged
        receipt = self.router.execute(
            ExecutionRequest(
                action=ExecutionAction.FILE_DIFF,
                project_root=task.project_root,
                mandate_id=task.mandate_id,
                args={
                    "worktree": active_worktree,
                    "path": path,
                    "staged": use_staged,
                },
            ),
            task.engine_id,
        )
        diff = ""
        if isinstance(receipt.payload, Mapping):
            value = receipt.payload.get("diff")
            if isinstance(value, str):
                diff = value
        return {
            "engine": receipt.engine,
            "ok": receipt.ok,
            "exit_code": receipt.exit_code,
            "path": path,
            "staged": use_staged,
            "basis": (
                "review-snapshot"
                if use_staged and has_current_review_snapshot
                else "staged" if use_staged else "working-tree"
            ),
            "diff": diff,
        }

    @staticmethod
    def execution_worktree(task: DivanTask) -> str | None:
        execution = task.metadata.get("execution")
        if not isinstance(execution, Mapping):
            return None
        receipt_payload = execution.get("payload")
        if not isinstance(receipt_payload, Mapping):
            return None
        worktree = receipt_payload.get("worktree")
        if not isinstance(worktree, str) or not worktree.strip():
            return None
        return worktree.strip()

    @staticmethod
    def serialize_tasks(tasks: Iterable[DivanTask]) -> list[dict[str, Any]]:
        return [task.to_dict() for task in tasks]


def _same_worktree(left: str, right: str) -> bool:
    try:
        return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
    except OSError:
        return False
