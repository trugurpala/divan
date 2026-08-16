"""Keep a source tree still while a canonical verification is reading it.

A verification that runs while an edit lands in the same tree reports
failures that belong to neither the old code nor the new. The guard is a
small lock file under the tree's ``.divan`` directory. It writes only that
file, never a tracked one, and it never removes a lock whose holder is still
alive. Liveness is judged with the same PID-reuse-safe primitive the attempt
store uses, so a recycled pid cannot make a dead holder look alive.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

from .attempt_store import process_start_token
from .project_os import _pid_is_live, _project_identity

LOCK_NAME = "verification.lock"
SCHEMA_VERSION = 1
LOCK_FIELDS = frozenset(
    {
        "schema_version",
        "pid",
        "process_start_token",
        "acquired_at",
        "purpose",
        "tree_digest",
    }
)


class GuardState(str, Enum):
    """What the lock file says about the tree, without changing anything."""

    FREE = "free"
    HELD_LIVE = "held_live"
    STALE = "stale"
    MALFORMED = "malformed"


class VerificationGuardError(RuntimeError):
    """The guard could not be honoured; the caller must not mutate the tree."""


@dataclass(frozen=True)
class LockHolder:
    """Who wrote the lock, as recorded in the file."""

    pid: int
    process_start_token: str
    acquired_at: str
    purpose: str
    tree_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "pid": self.pid,
            "process_start_token": self.process_start_token,
            "acquired_at": self.acquired_at,
            "purpose": self.purpose,
            "tree_digest": self.tree_digest,
        }


@dataclass(frozen=True)
class GuardStatus:
    """Read-only answer to "may I mutate this tree right now?"."""

    state: GuardState
    lock_path: Path
    reason: str
    holder: LockHolder | None = None

    @property
    def mutation_allowed(self) -> bool:
        return self.state is not GuardState.HELD_LIVE


@dataclass(frozen=True)
class GuardLease:
    """Proof that this process holds the tree. Only its holder may release it."""

    tree: Path
    lock_path: Path
    holder: LockHolder
    #: The lock that was on disk before this lease took the tree over, if any.
    recovered: GuardStatus | None = None


@dataclass(frozen=True)
class AcquireResult:
    lease: GuardLease | None
    reason: str
    refused_by: GuardStatus | None = None


@dataclass(frozen=True)
class ReleaseReport:
    released: bool
    reason: str


def lock_path_for(tree: Path) -> Path:
    return Path(tree) / ".divan" / LOCK_NAME


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _own_holder(tree: Path, purpose: str) -> LockHolder:
    pid = os.getpid()
    return LockHolder(
        pid=pid,
        process_start_token=process_start_token(pid),
        acquired_at=_utc_now(),
        purpose=purpose,
        tree_digest=_project_identity(Path(tree)),
    )


def _parse_holder(content: bytes) -> LockHolder | None:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or set(payload) != LOCK_FIELDS:
        return None
    if payload["schema_version"] != SCHEMA_VERSION:
        return None
    pid = payload["pid"]
    if type(pid) is not int or pid <= 0:
        return None
    strings = ("process_start_token", "acquired_at", "purpose", "tree_digest")
    if not all(isinstance(payload[key], str) and payload[key] for key in strings):
        return None
    return LockHolder(
        pid=pid,
        process_start_token=payload["process_start_token"],
        acquired_at=payload["acquired_at"],
        purpose=payload["purpose"],
        tree_digest=payload["tree_digest"],
    )


def _read_lock(path: Path) -> tuple[bytes | None, LockHolder | None]:
    """Return the raw bytes and the parsed holder; ``(None, None)`` when absent."""
    try:
        if path.is_symlink():
            return b"", None
        content = path.read_bytes()
    except FileNotFoundError:
        return None, None
    except OSError:
        return b"", None
    return content, _parse_holder(content)


def _classify(path: Path, content: bytes | None, holder: LockHolder | None) -> GuardStatus:
    if content is None:
        return GuardStatus(GuardState.FREE, path, "no verification lock")
    if holder is None:
        return GuardStatus(
            GuardState.MALFORMED, path, "lock file is not a valid verification lock"
        )
    if _pid_is_live(holder.pid, holder.process_start_token):
        return GuardStatus(
            GuardState.HELD_LIVE,
            path,
            f"held by live process {holder.pid} for {holder.purpose}",
            holder,
        )
    return GuardStatus(
        GuardState.STALE,
        path,
        f"holder process {holder.pid} is gone or its pid was reused",
        holder,
    )


def check(tree: Path) -> GuardStatus:
    """Report the guard state without acquiring, recovering or writing anything."""
    path = lock_path_for(tree)
    content, holder = _read_lock(path)
    return _classify(path, content, holder)


def _write_exclusive(path: Path, payload: bytes) -> bool:
    """Create the lock only if it does not exist yet. False when someone beat us."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return True


def _remove_if_unchanged(path: Path, observed: bytes) -> bool:
    """Remove a stale or malformed lock, but only the exact bytes we classified.

    A holder that appeared between our read and now keeps its lock; the caller
    re-reads and re-classifies rather than assuming the takeover succeeded.
    """
    current, _holder = _read_lock(path)
    if current is None:
        return True
    if current != observed:
        return False
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def try_acquire(tree: Path, purpose: str, *, attempts: int = 3) -> AcquireResult:
    """Take the tree if it is free or its lock is dead; refuse a live holder.

    A live holder is never removed. A stale lock, whether its process is gone
    or its pid now belongs to a different process, and a malformed lock are
    both recovered, and the lease records what was recovered so the caller can
    report it.
    """
    tree = Path(tree)
    path = lock_path_for(tree)
    path.parent.mkdir(parents=True, exist_ok=True)
    holder = _own_holder(tree, purpose)
    text = json.dumps(holder.to_dict(), ensure_ascii=False, indent=2) + "\n"
    payload = text.encode("utf-8")
    recovered: GuardStatus | None = None
    status: GuardStatus | None = None
    for _round in range(attempts):
        if _write_exclusive(path, payload):
            reason = f"recovered a {recovered.state.value} lock" if recovered else "tree was free"
            return AcquireResult(GuardLease(tree, path, holder, recovered), reason)
        content, existing = _read_lock(path)
        status = _classify(path, content, existing)
        if status.state is GuardState.HELD_LIVE:
            return AcquireResult(None, status.reason, status)
        if status.state is GuardState.FREE:
            continue
        if _remove_if_unchanged(path, content or b""):
            recovered = status
    detail = status.reason if status else "the lock kept changing"
    return AcquireResult(None, f"could not settle the lock: {detail}", status)


def acquire(tree: Path, purpose: str) -> GuardLease | None:
    """Return a lease when the tree can be held; ``None`` when a live process holds it.

    Use :func:`try_acquire` when the refusal reason is needed, or :func:`check`
    to inspect the holder before deciding.
    """
    return try_acquire(tree, purpose).lease


def release(lease: GuardLease) -> ReleaseReport:
    """Remove the lock only when this process wrote it and it is still ours."""
    own_pid = os.getpid()
    own_token = process_start_token(own_pid)
    if (lease.holder.pid, lease.holder.process_start_token) != (own_pid, own_token):
        return ReleaseReport(False, "lease belongs to another process; not released")
    content, on_disk = _read_lock(lease.lock_path)
    if content is None:
        return ReleaseReport(False, "no lock on disk; nothing released")
    if on_disk is None:
        return ReleaseReport(False, "lock on disk is malformed; left in place for check()")
    if (on_disk.pid, on_disk.process_start_token, on_disk.tree_digest) != (
        lease.holder.pid,
        lease.holder.process_start_token,
        lease.holder.tree_digest,
    ):
        return ReleaseReport(
            False, f"lock is now held by process {on_disk.pid}; not released"
        )
    if not _remove_if_unchanged(lease.lock_path, content):
        return ReleaseReport(False, "lock changed while releasing; not released")
    return ReleaseReport(True, "released")


@contextmanager
def held(tree: Path, purpose: str) -> Iterator[GuardLease]:
    """Hold the tree for the block; raise instead of running over a live holder."""
    result = try_acquire(tree, purpose)
    if result.lease is None:
        raise VerificationGuardError(result.reason)
    try:
        yield result.lease
    except BaseException:
        # The body's failure is the news; a refused release must not hide it.
        release(result.lease)
        raise
    report = release(result.lease)
    if not report.released:
        raise VerificationGuardError(report.reason)
