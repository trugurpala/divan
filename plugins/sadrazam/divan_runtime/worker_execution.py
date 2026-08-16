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
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .attempt_contract import AttemptRecord, AttemptState, FailureClass
from .attempt_store import (
    AttemptStore,
    next_attempt_id,
    process_start_token,
    utc_now,
)
from .worker_certification import certify_worker
from .worker_process import run_bounded

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
    #: The argument that tells this worker to read its instructions from stdin.
    #: The prompt never travels in argv: a command line is readable by every
    #: other process on the machine, and it has a length limit that real task
    #: context will exceed.
    stdin_marker: str = "-"


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
    #: Immutable name for accepted work, so a result can be pointed at later.
    result_commit: str | None = None
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
            "result_commit": self.result_commit,
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


class _AttemptTracker:
    """Keeps the stored attempt current while its worker is still running.

    Liveness and progress are recorded separately because the contract treats
    them separately: a process can be alive and stuck, and only the second
    signal distinguishes a slow worker from a hung one.
    """

    def __init__(self, store: AttemptStore, attempt: AttemptRecord) -> None:
        self._store = store
        self.attempt = attempt

    def alive(self) -> None:
        self._record(replace(self.attempt, heartbeat_at=utc_now()))

    def progress(self) -> None:
        moment = utc_now()
        self._record(
            replace(self.attempt, heartbeat_at=moment, last_progress_at=moment)
        )

    def _record(self, attempt: AttemptRecord) -> None:
        self.attempt = attempt
        self._store.save(attempt)


def _resolve_launcher(worker_id: str) -> tuple[WorkerCommand, str]:
    command = WORKER_COMMANDS.get(worker_id)
    if command is None:
        raise ValueError(f"no headless invocation is defined for {worker_id}")
    certificate = certify_worker(worker_id)
    if not certificate.certified or not certificate.executable:
        raise ValueError(f"{worker_id} is not certified for execution")
    return command, certificate.executable


#: Divan commits attempt results under its own name. The work was produced by
#: a worker under Divan's control, not typed by the owner, and a disposable
#: project may have no identity configured at all.
COMMITTER_NAME = "Divan"
COMMITTER_EMAIL = "attempt@divan.invalid"


def _commit_result(worktree: Path, attempt_id: str) -> str | None:
    """Give the accepted work an immutable name, or admit it has none."""
    committed = _git(
        worktree,
        "-c",
        f"user.name={COMMITTER_NAME}",
        "-c",
        f"user.email={COMMITTER_EMAIL}",
        "commit",
        "-m",
        f"attempt {attempt_id}",
    )
    if committed.returncode != 0:
        return None
    head = _git(worktree, "rev-parse", "HEAD")
    return head.stdout.strip() or None


def _notes_for(
    reading: WorktreeReading, result_commit: str | None, *, accepted: bool
) -> tuple[str, ...]:
    notes: list[str] = []
    if reading.unreadable:
        notes.append(
            "the worker wrote files this host may not read: "
            + ", ".join(reading.unreadable)
        )
    if reading.read_error:
        notes.append(reading.read_error)
    # Only meaningful when a commit was actually attempted; a rejected attempt
    # is not missing a result name, it never earned one.
    if accepted and result_commit is None:
        notes.append("the accepted work could not be committed in the worktree")
    return tuple(notes)


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
    command, executable = _resolve_launcher(worker_id)
    attempt_id = next_attempt_id(task_id, store.for_task(task_id))
    argv = [
        executable,
        *command.argv_prefix,
        *command.extra_args,
        command.stdin_marker,
    ]

    tracker: _AttemptTracker | None = None

    def _started(process: subprocess.Popen[str]) -> None:
        nonlocal tracker
        moment = utc_now()
        record = AttemptRecord(
            attempt_id=attempt_id,
            task_id=task_id,
            worker_id=worker_id,
            provider=worker_id,
            agent=worker_id,
            started_at=moment,
            heartbeat_at=moment,
            worktree=str(worktree),
            base_commit=base_commit,
            pid=process.pid,
            process_start_token=process_start_token(process.pid),
        )
        store.save(record)
        tracker = _AttemptTracker(store, record)

    def _alive() -> None:
        if tracker is not None:
            tracker.alive()

    def _progress() -> None:
        if tracker is not None:
            tracker.progress()

    started = time.monotonic()
    outcome = run_bounded(
        argv,
        cwd=worktree,
        stdin_text=prompt,
        timeout_seconds=timeout_seconds,
        on_start=_started,
        on_alive=_alive,
        on_progress=_progress,
    )
    duration = time.monotonic() - started
    if tracker is None:
        raise RuntimeError("the worker process never started")

    reading = worktree_changes(worktree)
    failure = _classify(outcome.exit_code, outcome.timed_out, reading)
    result_commit = _commit_result(worktree, attempt_id) if failure is None else None
    finished = utc_now()
    if failure is None:
        attempt = tracker.attempt.transition(
            AttemptState.COMPLETED,
            "worker finished and changed the worktree",
            at=finished,
            exit_code=outcome.exit_code,
            result_commit=result_commit,
        )
    else:
        attempt = tracker.attempt.transition(
            AttemptState.FAILED,
            "worker did not produce an accepted result",
            at=finished,
            failure_class=failure,
            exit_code=outcome.exit_code,
        )
    store.save(attempt)

    return ExecutionResult(
        attempt=attempt,
        exit_code=outcome.exit_code,
        stdout=outcome.stdout,
        stderr=outcome.stderr,
        changed_files=reading.changed,
        diff=reading.diff,
        duration_seconds=duration,
        timed_out=outcome.timed_out,
        unreadable_files=reading.unreadable,
        result_commit=result_commit,
        notes=_notes_for(reading, result_commit, accepted=failure is None),
    )
