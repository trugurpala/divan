"""Persist attempts, notice when one goes quiet, and decide what is safe next.

Liveness and progress are deliberately separate signals. A process can be
alive and stuck, and a process can be gone while its worktree still holds
work. A PID is not health, so the recorded process start token guards against
PID reuse before an attempt is ever called orphaned.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable

from .attempt_contract import (
    RETRYABLE_CLASSES,
    AttemptRecord,
    AttemptState,
    FailureClass,
)
from .project_os import _pid_is_live, _process_start_token

#: How long a worker may stay quiet before Divan suspects it, and before it is
#: treated as recoverable wreckage. Bounded and explicit so it can be tested.
DEFAULT_HEARTBEAT_GRACE = timedelta(minutes=2)
DEFAULT_STALL_LIMIT = timedelta(minutes=10)

#: A task may not burn attempts forever just because retrying is possible.
DEFAULT_MAX_ATTEMPTS = 3


def process_start_token(pid: int) -> str:
    """Return a PID-reuse guard token, or a truthful 'unavailable'."""
    return _process_start_token(pid) or "unavailable"


def _parse(moment: str | None) -> datetime | None:
    if not moment:
        return None
    try:
        return datetime.fromisoformat(moment)
    except ValueError:
        return None


class AttemptStore:
    """Small atomic JSON store for attempt records."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def path_for(self, attempt_id: str) -> Path:
        safe = attempt_id.strip()
        if not safe or any(char in safe for char in "/\\") or safe in {".", ".."}:
            raise ValueError("attempt_id must be a non-empty file-safe identifier")
        return self.root / f"{safe}.json"

    def save(self, attempt: AttemptRecord) -> Path:
        path = self.path_for(attempt.attempt_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(attempt.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(payload + "\n")
            temporary = Path(handle.name)
        os.replace(temporary, path)
        return path

    def load(self, attempt_id: str) -> AttemptRecord:
        path = self.path_for(attempt_id)
        return AttemptRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self) -> tuple[AttemptRecord, ...]:
        if not self.root.exists():
            return ()
        return tuple(self.load(path.stem) for path in sorted(self.root.glob("*.json")))

    def for_task(self, task_id: str) -> tuple[AttemptRecord, ...]:
        return tuple(item for item in self.list() if item.task_id == task_id)

    def open_attempt(self, task_id: str) -> AttemptRecord | None:
        for attempt in self.for_task(task_id):
            if attempt.open:
                return attempt
        return None


def worker_is_live(attempt: AttemptRecord) -> bool:
    """Answer whether this attempt's process still exists, guarding PID reuse."""
    if attempt.pid is None:
        return False
    return _pid_is_live(attempt.pid, attempt.process_start_token or "unavailable")


def classify_quiet_attempt(
    attempt: AttemptRecord,
    *,
    now: datetime,
    heartbeat_grace: timedelta = DEFAULT_HEARTBEAT_GRACE,
    stall_limit: timedelta = DEFAULT_STALL_LIMIT,
    live: bool | None = None,
) -> AttemptState:
    """Decide what a quiet attempt currently is, without changing it.

    A dead process is ORPHANED regardless of timers. A live process that has
    stopped making progress is SUSPECTED_STALLED first and only becomes
    recoverable wreckage once it passes the stall limit, so a slow worker is
    never mistaken for a dead one.
    """
    if attempt.state not in {AttemptState.RUNNING, AttemptState.SUSPECTED_STALLED}:
        return attempt.state
    alive = worker_is_live(attempt) if live is None else live
    if not alive:
        return AttemptState.ORPHANED

    progress = _parse(attempt.last_progress_at) or _parse(attempt.heartbeat_at)
    reference = progress or _parse(attempt.started_at)
    if reference is None:
        return attempt.state
    quiet_for = now - reference
    if quiet_for >= stall_limit:
        return AttemptState.RECOVERY_PENDING
    if quiet_for >= heartbeat_grace:
        return AttemptState.SUSPECTED_STALLED
    return AttemptState.RUNNING


def recovery_decision(
    attempt: AttemptRecord,
    *,
    prior_attempts: int,
    resume_supported: bool,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> tuple[str, str]:
    """Return the next safe action and why, without performing it.

    Returns one of ``resume``, ``replace`` or ``fail`` together with a reason.
    A circuit breaker stops a task burning attempts forever simply because
    retrying is technically possible.
    """
    failure = attempt.failure_class or FailureClass.UNKNOWN
    if failure not in RETRYABLE_CLASSES:
        return "fail", f"{failure.value} is not safe to retry"
    if prior_attempts >= max_attempts:
        return "fail", f"attempt budget of {max_attempts} is exhausted"
    if resume_supported and attempt.checkpoint_ref:
        return "resume", "worker reported a checkpoint and the provider can resume"
    return "replace", "no resumable checkpoint; a fresh attempt is safer"


def next_attempt_id(task_id: str, existing: Iterable[AttemptRecord]) -> str:
    return f"{task_id}-A{len(tuple(existing)) + 1:03d}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def attempt_summary(attempts: Iterable[AttemptRecord]) -> dict[str, Any]:
    """Project the attempt history for evidence and human status."""
    rows = tuple(attempts)
    return {
        "schema_version": 1,
        "total": len(rows),
        "open": sum(1 for item in rows if item.open),
        "replaced": sum(1 for item in rows if item.state is AttemptState.REPLACED),
        "orphaned": sum(1 for item in rows if item.state is AttemptState.ORPHANED),
        "completed": sum(1 for item in rows if item.state is AttemptState.COMPLETED),
        "providers": sorted({item.provider for item in rows}),
        "attempt_ids": [item.attempt_id for item in rows],
    }
