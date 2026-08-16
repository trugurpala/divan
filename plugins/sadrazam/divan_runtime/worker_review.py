"""Have a second worker judge the first one's work without being able to change it.

Independence is treated as a property of the process rather than a promise in a
prompt. The reviewer is a separate process that carries none of the writer's
session, and it runs under a sandbox that denies writing. Both claims are
checked after the fact: the pids are compared, and the worktree is read before
and after so a reviewer that did change something cannot be described as
read-only.

Where a second vendor is not available, that is recorded as a limitation rather
than dressed up as independence.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .worker_certification import certify_worker
from .worker_execution import WorkerCommand, build_argv
from .worker_process import run_bounded
from .worktree_reading import git_in_worktree

REVIEW_SCHEMA_VERSION = 1

#: A review reads; it does not need as long as building does.
DEFAULT_REVIEW_TIMEOUT_SECONDS = 600


class Independence(StrEnum):
    PROVEN = "proven"
    #: Checked and found false.
    ABSENT = "absent"
    #: Could not be established on this machine at all.
    UNAVAILABLE = "unavailable"


class WriteAccess(StrEnum):
    DENIED = "denied"
    GRANTED = "granted"
    #: The tree could not be read, so nothing about write access was observed.
    UNOBSERVED = "unobserved"


#: How a reviewer is invoked. read-only is the whole point: the reviewer may
#: read the work and may not touch it.
REVIEW_COMMANDS: dict[str, WorkerCommand] = {
    "codex": WorkerCommand(
        worker_id="codex",
        argv_prefix=("exec",),
        extra_args=("--skip-git-repo-check", "--sandbox", "read-only"),
    ),
}


@dataclass(frozen=True)
class ReviewOutcome:
    reviewer_id: str
    writer_id: str
    findings: str
    provider_independence: Independence
    process_independence: Independence
    write_access: WriteAccess
    writer_pid: int | None
    reviewer_pid: int | None
    exit_code: int | None
    duration_seconds: float
    timed_out: bool = False
    notes: tuple[str, ...] = ()

    @property
    def usable(self) -> bool:
        """A review only counts when it finished and could not edit its subject.

        A reviewer that died, ran out of time, or printed an authentication
        error still leaves text behind, and that text is not a review.
        """
        return (
            self.exit_code == 0
            and not self.timed_out
            and self.write_access is WriteAccess.DENIED
            and self.process_independence is Independence.PROVEN
            and bool(self.findings.strip())
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = REVIEW_SCHEMA_VERSION
        payload["provider_independence"] = self.provider_independence.value
        payload["process_independence"] = self.process_independence.value
        payload["write_access"] = self.write_access.value
        payload["usable"] = self.usable
        payload["notes"] = list(self.notes)
        return payload


def _worktree_fingerprint(worktree: Path) -> tuple[str, str] | None:
    """What the tree looks like, or nothing when it could not be read.

    Both git calls are checked. A failed call returns empty output, and two
    equal emptinesses would otherwise read as proof that nothing changed.
    """
    head = git_in_worktree(worktree, "rev-parse", "HEAD")
    status = git_in_worktree(worktree, "status", "--porcelain")
    if head.returncode != 0 or status.returncode != 0:
        return None
    return head.stdout.strip(), status.stdout.strip()


def _provider_independence(writer_id: str, reviewer_id: str) -> Independence:
    if writer_id != reviewer_id:
        return Independence.PROVEN
    # The same vendor reviewing itself is not vendor independence. Say so.
    return Independence.UNAVAILABLE


def run_independent_review(
    *,
    worktree: Path,
    prompt: str,
    writer_id: str,
    writer_pid: int | None = None,
    reviewer_id: str = "codex",
    timeout_seconds: int = DEFAULT_REVIEW_TIMEOUT_SECONDS,
) -> ReviewOutcome:
    """Run a fresh reviewer over work it is not permitted to change."""
    command = REVIEW_COMMANDS.get(reviewer_id)
    if command is None:
        raise ValueError(f"no review invocation is defined for {reviewer_id}")
    certificate = certify_worker(reviewer_id)
    if not certificate.certified or not certificate.executable:
        raise ValueError(f"{reviewer_id} is not certified to review")

    before = _worktree_fingerprint(worktree)
    reviewer_pid: int | None = None

    def _started(process: Any) -> None:
        nonlocal reviewer_pid
        reviewer_pid = process.pid

    started = time.monotonic()
    outcome = run_bounded(
        build_argv(certificate.executable, command),
        cwd=worktree,
        stdin_text=prompt,
        timeout_seconds=timeout_seconds,
        on_start=_started,
    )
    duration = time.monotonic() - started
    after = _worktree_fingerprint(worktree)

    notes: list[str] = []
    if before is None or after is None:
        write_access = WriteAccess.UNOBSERVED
        notes.append("the worktree could not be read, so write access is unproven")
    elif after != before:
        write_access = WriteAccess.GRANTED
        notes.append("the reviewer changed the worktree it was asked to judge")
    else:
        write_access = WriteAccess.DENIED

    process_independence = Independence.PROVEN
    if reviewer_pid is None:
        process_independence = Independence.UNAVAILABLE
        notes.append("the reviewer process was never observed")
    elif writer_pid is not None and reviewer_pid == writer_pid:
        process_independence = Independence.ABSENT
        notes.append("the reviewer ran in the writer's own process")

    provider = _provider_independence(writer_id, reviewer_id)
    if provider is Independence.UNAVAILABLE:
        notes.append(
            f"writer and reviewer are both {reviewer_id};"
            " a second vendor is not available on this machine"
        )
    if outcome.timed_out:
        notes.append("the review did not finish inside its bound")

    # Codex writes its transcript to stderr and its answer there too, so the
    # findings are whichever stream actually carried text.
    findings = outcome.stdout.strip() or outcome.stderr.strip()

    return ReviewOutcome(
        reviewer_id=reviewer_id,
        writer_id=writer_id,
        findings=findings,
        provider_independence=provider,
        process_independence=process_independence,
        write_access=write_access,
        writer_pid=writer_pid,
        reviewer_pid=reviewer_pid,
        exit_code=outcome.exit_code,
        duration_seconds=duration,
        timed_out=outcome.timed_out,
        notes=tuple(notes),
    )
