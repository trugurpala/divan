from __future__ import annotations

from collections.abc import Mapping

from .review_gate import CheckResult, GateVerdict, ReviewDecision
from .task_model import DivanTask


def next_execution_attempt(task: DivanTask) -> int:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        return 1
    attempt = execution.get("attempt")
    if isinstance(attempt, int) and not isinstance(attempt, bool) and attempt >= 1:
        return attempt + 1
    return 2


def execution_worktree(task: DivanTask) -> str:
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


def worker_agent(task: DivanTask) -> str | None:
    execution = task.metadata.get("execution")
    if not isinstance(execution, Mapping):
        return None
    payload = execution.get("payload")
    if not isinstance(payload, Mapping):
        return None
    value = payload.get("agent")
    return value.strip() if isinstance(value, str) and value.strip() else None


def execution_ok(task: DivanTask) -> bool:
    execution = task.metadata.get("execution")
    return isinstance(execution, Mapping) and execution.get("ok") is True


def require_automated_pass(task: DivanTask) -> None:
    value = task.metadata.get("automated_review")
    if not isinstance(value, Mapping):
        raise ValueError("approval requires an independent automated review")
    reviewer = value.get("reviewer")
    verdict = value.get("verdict")
    if reviewer not in {"claude", "codex"} or verdict != "PASS":
        raise ValueError("approval requires PASS from Claude or Codex independent review")


def review_from_task(task: DivanTask) -> ReviewDecision:
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
