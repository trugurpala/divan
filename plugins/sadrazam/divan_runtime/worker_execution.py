"""Run a real coding worker under Divan's control.

Divan starts the process, owns the attempt record, and reads the result from
the worktree. A worker's own claim that it finished is not a result: only a
diff, a changed file set and an exit code are.

The launcher comes from the certified discovery path, so a Windows shell shim
or an extensionless script is never executed by mistake.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .attempt_contract import AttemptRecord, AttemptState, FailureClass
from .attempt_store import AttemptStore, process_start_token, utc_now
from .worker_certification import certify_worker

EXECUTION_SCHEMA_VERSION = 1

#: A single bounded attempt. Long enough for real work, short enough to notice.
DEFAULT_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class WorkerCommand:
    """How one worker is invoked headlessly."""

    worker_id: str
    argv_prefix: tuple[str, ...]
    #: Passed so the worker does not refuse a fresh worktree.
    extra_args: tuple[str, ...] = ()


#: Non-interactive invocation for each certified worker.
WORKER_COMMANDS: dict[str, WorkerCommand] = {
    "codex": WorkerCommand(
        worker_id="codex",
        argv_prefix=("exec",),
        # workspace-write lets the worker create files inside the worktree it
        # was given and nowhere else. Full access and approval bypass are
        # deliberately not used: the sandbox is the boundary, not the prompt.
        extra_args=("--skip-git-repo-check", "--sandbox", "workspace-write"),
    ),
}


@dataclass(frozen=True)
class WorktreeReading:
    """What the host could actually read back out of the worktree."""

    changed: tuple[str, ...]
    diff: str
    #: Files the worker wrote that the host is not permitted to read.
    unreadable: tuple[str, ...] = ()
    #: Why the read failed, when git would not name the files.
    read_error: str | None = None

    @property
    def readable(self) -> bool:
        return not self.unreadable and self.read_error is None


@dataclass(frozen=True)
class ExecutionResult:
    attempt: AttemptRecord
    exit_code: int | None
    stdout: str
    stderr: str
    changed_files: tuple[str, ...]
    diff: str
    duration_seconds: float
    timed_out: bool = False
    unreadable_files: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def produced_work(self) -> bool:
        """True only when the worktree changed and the host could read it."""
        return bool(self.changed_files) and not self.unreadable_files

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "attempt": self.attempt.to_dict(),
            "exit_code": self.exit_code,
            "changed_files": list(self.changed_files),
            "unreadable_files": list(self.unreadable_files),
            "diff_lines": len(self.diff.splitlines()),
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
            "produced_work": self.produced_work,
            "notes": list(self.notes),
            # stdout and stderr are kept out of the manifest; they go to
            # evidence separately so a transcript never becomes the result.
        }


def _git(worktree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(worktree), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


#: How git reports a file it was not allowed to open.
_UNREADABLE_MARKER = 'error: open("'


def _unreadable_paths(stderr: str) -> tuple[str, ...]:
    """Names of the files git was refused access to, as git reported them."""
    paths: list[str] = []
    for line in stderr.splitlines():
        start = line.find(_UNREADABLE_MARKER)
        if start == -1:
            continue
        rest = line[start + len(_UNREADABLE_MARKER):]
        end = rest.find('")')
        paths.append(rest if end == -1 else rest[:end])
    return tuple(paths)


def worktree_changes(worktree: Path) -> WorktreeReading:
    """Read back what the worker did, or report why it could not be read.

    A sandboxed worker can create files the host has no permission to open.
    Staging then silently fails and the diff comes back empty, which would
    otherwise look exactly like a worker that produced nothing.
    """
    status = _git(worktree, "status", "--porcelain")
    changed = tuple(
        line[3:].strip()
        for line in status.stdout.splitlines()
        if line.strip()
    )
    # Include untracked content so a newly created file counts as work.
    staged = _git(worktree, "add", "-A")
    unreadable: tuple[str, ...] = ()
    read_error: str | None = None
    if staged.returncode != 0:
        unreadable = _unreadable_paths(staged.stderr)
        if not unreadable:
            first = staged.stderr.strip().splitlines()
            read_error = first[0] if first else "git could not stage the worktree"
    diff = _git(worktree, "diff", "--cached")
    return WorktreeReading(
        changed=changed,
        diff=diff.stdout,
        unreadable=unreadable,
        read_error=read_error,
    )


def _classify(
    exit_code: int | None, timed_out: bool, reading: WorktreeReading
) -> FailureClass | None:
    """Decide whether this attempt actually delivered.

    A clean exit code is not a result. A worker that ran happily and changed
    nothing did not do the job, and calling that COMPLETED would be exactly
    the fake pass this system exists to prevent. Work the host cannot read is
    not a result either, however willing the worker was.
    """
    if timed_out:
        return FailureClass.WORKER_STALLED
    if exit_code is None:
        return FailureClass.WORKER_LOST
    if not reading.readable:
        return FailureClass.ENVIRONMENT
    if exit_code != 0:
        return FailureClass.WORK_REJECTED if reading.changed else FailureClass.ENVIRONMENT
    if not reading.changed:
        return FailureClass.WORK_REJECTED
    return None


def run_worker_attempt(
    *,
    task_id: str,
    worker_id: str,
    prompt: str,
    worktree: Path,
    store: AttemptStore,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    base_commit: str | None = None,
) -> ExecutionResult:
    """Start one real worker attempt and read its result from the worktree."""
    command = WORKER_COMMANDS.get(worker_id)
    if command is None:
        raise ValueError(f"no headless invocation is defined for {worker_id}")

    certificate = certify_worker(worker_id)
    if not certificate.certified or not certificate.executable:
        raise ValueError(f"{worker_id} is not certified for execution")

    attempt_id = f"{task_id}-A{len(store.for_task(task_id)) + 1:03d}"
    argv = [
        certificate.executable,
        *command.argv_prefix,
        *command.extra_args,
        prompt,
    ]

    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=str(worktree),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    attempt = AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        worker_id=worker_id,
        provider=worker_id,
        agent=worker_id,
        started_at=utc_now(),
        heartbeat_at=utc_now(),
        worktree=str(worktree),
        base_commit=base_commit,
        pid=process.pid,
        process_start_token=process_start_token(process.pid),
    )
    store.save(attempt)

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate()
    duration = time.monotonic() - started

    reading = worktree_changes(worktree)
    failure = _classify(process.returncode, timed_out, reading)
    finished = utc_now()
    if failure is None:
        attempt = attempt.transition(
            AttemptState.COMPLETED,
            "worker finished and changed the worktree",
            at=finished,
            exit_code=process.returncode,
        )
    else:
        attempt = attempt.transition(
            AttemptState.FAILED,
            "worker did not produce an accepted result",
            at=finished,
            failure_class=failure,
            exit_code=process.returncode,
        )
    store.save(attempt)

    notes: list[str] = []
    if reading.unreadable:
        notes.append(
            "the worker wrote files this host may not read: "
            + ", ".join(reading.unreadable)
        )
    if reading.read_error:
        notes.append(reading.read_error)

    return ExecutionResult(
        attempt=attempt,
        exit_code=process.returncode,
        stdout=stdout or "",
        stderr=stderr or "",
        changed_files=reading.changed,
        diff=reading.diff,
        duration_seconds=duration,
        timed_out=timed_out,
        unreadable_files=reading.unreadable,
        notes=tuple(notes),
    )
