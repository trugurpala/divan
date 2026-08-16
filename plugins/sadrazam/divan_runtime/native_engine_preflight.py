from __future__ import annotations

from .execution_contract import ExecutionReceipt, ExecutionRequest


def stale_capability_receipt(
    request: ExecutionRequest,
    engine_id: str,
    agent: str,
    binary: str,
    current_binary: str | None,
) -> ExecutionReceipt | None:
    """Return a fail-closed receipt when a live capability probe changed."""
    if current_binary == binary:
        return None
    return ExecutionReceipt(
        engine=engine_id,
        action=request.action,
        ok=False,
        exit_code=3,
        payload={"agent": agent},
        stdout="",
        stderr="agent capability changed since the engine was initialized",
        argv=("<agent-capability-probe>", agent),
        mandate_id=request.mandate_id,
    )
