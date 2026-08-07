from __future__ import annotations

from typing import Any

from .execution_contract import ExecutionAction, ExecutionReceipt, ExecutionRequest
from .orca_engine import ExecutionAuthority, OrcaEngine


class OrcaExecutionAdapter:
    """Expose OrcaEngine through Divan's generic ExecutionEngine protocol."""

    engine_id = "orca"

    def __init__(self, engine: OrcaEngine | None = None) -> None:
        self.engine = engine or OrcaEngine()

    def execute(self, request: ExecutionRequest) -> ExecutionReceipt:
        authority = ExecutionAuthority(
            execute=bool(request.mandate_id),
            mandate_id=request.mandate_id,
        )
        action = request.action
        args = dict(request.args)

        if action is ExecutionAction.STATUS:
            result = self.engine.status()
        elif action is ExecutionAction.WORKTREE_LIST:
            result = self.engine.worktree_list(_required(args, "repo_selector"))
        elif action is ExecutionAction.WORKTREE_CREATE:
            result = self.engine.worktree_create(
                name=_required(args, "name"),
                repo_selector=args.get("repo_selector"),
                agent=args.get("agent"),
                prompt=args.get("prompt"),
                setup=args.get("setup", "inherit"),
                authority=authority,
            )
        elif action is ExecutionAction.TERMINAL_READ:
            result = self.engine.terminal_read(_required(args, "terminal"))
        elif action is ExecutionAction.TERMINAL_WAIT:
            timeout_ms = args.get("timeout_ms", 300_000)
            if not isinstance(timeout_ms, int):
                raise ValueError("timeout_ms must be an integer")
            result = self.engine.terminal_wait(
                _required(args, "terminal"),
                timeout_ms=timeout_ms,
            )
        elif action is ExecutionAction.FILE_DIFF:
            result = self.engine.file_diff(
                path=_required(args, "path"),
                worktree=args.get("worktree", "active"),
                staged=bool(args.get("staged", False)),
            )
        elif action is ExecutionAction.SNAPSHOT:
            result = self.engine.snapshot(args.get("worktree", "active"))
        else:
            raise ValueError(f"unsupported Orca action: {action.value}")

        return ExecutionReceipt(
            engine=self.engine_id,
            action=action,
            ok=result.ok,
            exit_code=result.exit_code,
            payload=result.payload,
            stdout=result.stdout,
            stderr=result.stderr,
            argv=result.argv,
            mandate_id=result.mandate_id,
        )


def _required(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required execution argument: {key}")
    return value
