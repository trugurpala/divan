from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from .evidence import EvidenceRecord, build_evidence
from .execution_contract import ExecutionReceipt
from .task_model import DivanTask, TaskState


@dataclass(frozen=True)
class ExecutionAttempt:
    running: DivanTask
    attempt: int
    worktree_name: str


def prepare_execution_attempt(
    task: DivanTask,
    *,
    worktree_name: str,
    agent: str | None,
) -> ExecutionAttempt:
    attempt = _next_execution_attempt(task)
    execution_name = (
        worktree_name if attempt == 1 else f"{worktree_name}-attempt-{attempt}"
    )
    metadata = _reset_active_execution(task.metadata)
    metadata["execution_pending"] = {
        "attempt": attempt,
        "worktree_name": execution_name,
        "agent": agent,
    }
    running = replace(
        task.transition(TaskState.RUNNING, f"execution attempt {attempt} started"),
        metadata=metadata,
    )
    return ExecutionAttempt(running, attempt, execution_name)


def complete_execution_attempt(
    pending: ExecutionAttempt,
    receipt: ExecutionReceipt,
) -> DivanTask:
    record = {
        "engine": receipt.engine,
        "ok": receipt.ok,
        "exit_code": receipt.exit_code,
        "payload": receipt.payload,
        "attempt": pending.attempt,
        "worktree_name": pending.worktree_name,
    }
    metadata = dict(pending.running.metadata)
    metadata.pop("execution_pending", None)
    metadata["execution"] = record
    history = _execution_history(metadata)
    history.append(record)
    metadata["execution_history"] = history
    return replace(pending.running, engine_id=receipt.engine, metadata=metadata)


def execution_attempt_evidence(
    pending: ExecutionAttempt,
    receipt: ExecutionReceipt,
) -> EvidenceRecord:
    return build_evidence(
        pending.running.task_id,
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
            "attempt": pending.attempt,
            "worktree_name": pending.worktree_name,
        },
    )


def recover_interrupted_attempt(task: DivanTask) -> tuple[DivanTask, EvidenceRecord]:
    _require_recoverable(task)
    metadata = dict(task.metadata)
    pending = _pending_execution(metadata)
    attempt = _pending_attempt(pending)
    worktree_name = _pending_worktree(pending, task.task_id)
    agent = _pending_agent(pending)
    record = _interrupted_record(task, attempt, worktree_name, agent)
    metadata.pop("execution_pending", None)
    metadata["execution"] = record
    history = _execution_history(metadata)
    history.append(record)
    metadata["execution_history"] = history
    prepared = replace(task, metadata=metadata)
    recovered = prepared.transition(
        TaskState.RETRY,
        f"execution attempt {attempt} interrupted; explicit retry required",
    )
    evidence = build_evidence(
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
    return recovered, evidence


def _reset_active_execution(metadata: Mapping[str, Any]) -> dict[str, Any]:
    clean = dict(metadata)
    for key in ("execution", "review_snapshot", "automated_review", "review"):
        clean.pop(key, None)
    return clean


def _next_execution_attempt(task: DivanTask) -> int:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        return 1
    attempt = execution.get("attempt")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt >= 1:
        return attempt + 1
    return 2


def _execution_history(metadata: Mapping[str, Any]) -> list[Any]:
    value = metadata.get("execution_history")
    return list(value) if isinstance(value, list) else []


def _require_recoverable(task: DivanTask) -> None:
    if task.state is not TaskState.RUNNING:
        raise ValueError("only a running task can be recovered as interrupted")
    if isinstance(task.metadata.get("execution"), Mapping):
        raise ValueError(
            "task already has an execution receipt; review it instead of recovering it"
        )


def _pending_execution(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    value = metadata.get("execution_pending")
    return value if isinstance(value, Mapping) else {}


def _pending_attempt(pending: Mapping[str, Any]) -> int:
    value = pending.get("attempt")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    return 1


def _pending_worktree(pending: Mapping[str, Any], fallback: str) -> str:
    value = pending.get("worktree_name")
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _pending_agent(pending: Mapping[str, Any]) -> str | None:
    value = pending.get("agent")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _interrupted_record(
    task: DivanTask,
    attempt: int,
    worktree_name: str,
    agent: str | None,
) -> dict[str, Any]:
    return {
        "engine": task.engine_id or "unknown",
        "ok": False,
        "exit_code": None,
        "payload": {},
        "attempt": attempt,
        "worktree_name": worktree_name,
        "agent": agent,
        "interrupted": True,
    }
