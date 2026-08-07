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
            result = self.engine.status(cwd=request.project_root)
        elif action is ExecutionAction.WORKTREE_LIST:
            result = self.engine.worktree_list(cwd=request.project_root)
        elif action is ExecutionAction.WORKTREE_CREATE:
            result = self.engine.worktree_create(
                name=_required(args, "name"),
                repo_selector=args.get("repo_selector"),
                agent=args.get("agent"),
                prompt=args.get("prompt"),
                authority=authority,
                cwd=request.project_root,
            )
        elif action is ExecutionAction.TERMINAL_READ:
            result = self.engine.terminal_read(
                terminal_id=_required(args, "terminal_id"),
                cwd=request.project_root,
            )
        elif action is ExecutionAction.TERMINAL_WAIT:
            result = self.engine.terminal_wait(
                terminal_id=_required(args, "terminal_id"),
                cwd=request.project_root,
            )
        elif action is ExecutionAction.FILE_DIFF:
            result = self.engine.file_diff(
                worktree=_required(args, "worktree"),
                cwd=request.project_root,
            )
        elif action is ExecutionAction.SNAPSHOT:
            result = self.engine.snapshot(cwd=request.project_root)
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
