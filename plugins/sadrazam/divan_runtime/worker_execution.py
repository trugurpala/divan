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
from .worker_process import ProcessOutcome, run_bounded
from .worktree_reading import (
    WorktreeReading,
    commit_result,
    worktree_changes,
    worktree_snapshot,
)

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


#: What every attempt is told about the circumstances it runs in.
#:
#: A worker that stops to ask whether it may proceed asks into a closed pipe:
#: Divan writes the task and closes stdin, so no answer can arrive. The worker
#: then exits cleanly having produced nothing, and the attempt is recorded as
#: rejected work when in truth the work was never attempted.
#:
#: This was observed: a repair attempt returned a correct plan, ended with "do
#: you approve applying this plan?", and produced no files. It is stated as a
#: fact about the environment rather than fixed with an approval-bypass flag,
#: because the sandbox is the boundary and loosening it to stop a worker asking
#: questions would trade a real protection for a prompt.
UNATTENDED_CONTRACT = """You are running unattended. Nobody is reading your
output while you work and no answer can reach you: the task was written to your
input and the stream is closed. Do not ask for approval, confirmation or a
choice, and do not stop at a plan and wait. Decide, act, and finish the work.

If the task is genuinely impossible or already done, say so plainly and stop;
that is a result. Asking a question is not a result, because there is nobody to
answer it.
"""


def contracted_prompt(prompt: str) -> str:
    """Put the unattended contract in front of the task."""
    return f"{UNATTENDED_CONTRACT}\n{prompt}"


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
    #: Whether the tree changed during this attempt, not merely whether it
    #: differs from its last commit. Work an earlier attempt left behind is
    #: not this attempt's work.
    produced: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def produced_work(self) -> bool:
        """True only when this attempt changed the tree and it could be read."""
        return self.produced and not self.unreadable_files

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
            "produced": self.produced,
            "produced_work": self.produced_work,
            "notes": list(self.notes),
            # stdout and stderr are kept out of the manifest; they go to
            # evidence separately so a transcript never becomes the result.
        }


def build_argv(executable: str, command: WorkerCommand) -> list[str]:
    """The exact command line a worker is started with.

    The prompt is deliberately absent. It goes down stdin instead, because a
    command line is readable by every other process on this machine and has a
    length limit that real compiled task context will exceed.
    """
    return [
        executable,
        *command.argv_prefix,
        *command.extra_args,
        command.stdin_marker,
    ]


def _classify(
    outcome: ProcessOutcome, reading: WorktreeReading, *, produced: bool
) -> FailureClass | None:
    """Decide whether this attempt actually delivered.

    A clean exit code is not a result. A worker that ran happily and changed
    nothing did not do the job, and calling that COMPLETED would be exactly
    the fake pass this system exists to prevent. Work the host cannot read is
    not a result either, however willing the worker was, and neither is work
    that was already sitting in the worktree before this attempt started.
    """
    if outcome.timed_out:
        return FailureClass.WORKER_STALLED
    if outcome.exit_code is None:
        return FailureClass.WORKER_LOST
    if outcome.stdin_error is not None:
        # The worker never received the task, so nothing it did answers it.
        return FailureClass.ENVIRONMENT
    if not reading.readable:
        return FailureClass.ENVIRONMENT
    if outcome.exit_code != 0:
        return FailureClass.WORK_REJECTED if produced else FailureClass.ENVIRONMENT
    if not produced:
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


def _notes_for(
    reading: WorktreeReading,
    result_commit: str | None,
    *,
    accepted: bool,
    stdin_error: str | None = None,
) -> tuple[str, ...]:
    notes: list[str] = []
    if stdin_error is not None:
        notes.append(stdin_error)
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
    argv = build_argv(executable, command)

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

    before = worktree_snapshot(worktree)
    started = time.monotonic()
    outcome = run_bounded(
        argv,
        cwd=worktree,
        stdin_text=contracted_prompt(prompt),
        timeout_seconds=timeout_seconds,
        on_start=_started,
        on_alive=_alive,
        on_progress=_progress,
    )
    duration = time.monotonic() - started
    if tracker is None:
        raise RuntimeError("the worker process never started")

    # Read the tree before staging, so what this attempt did is separable from
    # whatever an earlier attempt left behind.
    produced = worktree_snapshot(worktree) != before
    reading = worktree_changes(worktree)
    failure = _classify(outcome, reading, produced=produced)
    result_commit = commit_result(worktree, attempt_id) if failure is None else None
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
        produced=produced,
        notes=_notes_for(
            reading,
            result_commit,
            accepted=failure is None,
            stdin_error=outcome.stdin_error,
        ),
    )
