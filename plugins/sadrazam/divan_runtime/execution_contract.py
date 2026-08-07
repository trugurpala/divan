from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Protocol, Sequence


class ExecutionAction(StrEnum):
    STATUS = "status"
    WORKTREE_LIST = "worktree.list"
    WORKTREE_CREATE = "worktree.create"
    TERMINAL_READ = "terminal.read"
    TERMINAL_WAIT = "terminal.wait"
    FILE_DIFF = "file.diff"
    SNAPSHOT = "snapshot"


READ_ONLY_ACTIONS = {
    ExecutionAction.STATUS,
    ExecutionAction.WORKTREE_LIST,
    ExecutionAction.TERMINAL_READ,
    ExecutionAction.TERMINAL_WAIT,
    ExecutionAction.FILE_DIFF,
    ExecutionAction.SNAPSHOT,
}


@dataclass(frozen=True)
class ExecutionRequest:
    action: ExecutionAction
    project_root: str | None = None
    mandate_id: str | None = None
    args: Mapping[str, Any] = field(default_factory=dict)

    @property
    def mutating(self) -> bool:
        return self.action not in READ_ONLY_ACTIONS


@dataclass(frozen=True)
class ExecutionReceipt:
    engine: str
    action: ExecutionAction
    ok: bool
    exit_code: int
    payload: Any
    stdout: str
    stderr: str
    argv: Sequence[str]
    mandate_id: str | None = None


class ExecutionEngine(Protocol):
    engine_id: str

    def execute(self, request: ExecutionRequest) -> ExecutionReceipt: ...


class ExecutionPolicyError(RuntimeError):
    """Raised when Divan policy prevents execution before an engine is called."""


def require_mandate(request: ExecutionRequest) -> None:
    if request.mutating and not request.mandate_id:
        raise ExecutionPolicyError(
            f"mutating action {request.action.value!r} requires mandate_id"
        )
