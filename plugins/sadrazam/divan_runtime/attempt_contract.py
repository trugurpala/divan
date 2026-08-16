"""One execution attempt, as a first-class record.

A Task is what the agency promised. An Attempt is one worker's try at it.
Collapsing the two is how a stalled worker silently becomes a failed task, and
how a replacement worker quietly loses the history of what came before.

An attempt therefore carries its own identity, its own lifecycle and its own
evidence, and never redefines the task's acceptance contract.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
from typing import Any, Mapping

ATTEMPT_SCHEMA_VERSION = 1


class AttemptState(StrEnum):
    RUNNING = "running"
    #: Heartbeat or progress went quiet past the policy window; not yet proven dead.
    SUSPECTED_STALLED = "suspected-stalled"
    #: The worker process is provably gone and the attempt never finished.
    ORPHANED = "orphaned"
    #: Divan has taken ownership of the wreckage and is deciding what to do.
    RECOVERY_PENDING = "recovery-pending"
    RESUMED = "resumed"
    REPLACED = "replaced"
    FAILED = "failed"
    COMPLETED = "completed"


#: States after which no further work happens under this attempt id.
TERMINAL_STATES = frozenset(
    {
        AttemptState.RESUMED,
        AttemptState.REPLACED,
        AttemptState.FAILED,
        AttemptState.COMPLETED,
    }
)

#: States that still describe a live or recoverable attempt.
OPEN_STATES = frozenset(
    {
        AttemptState.RUNNING,
        AttemptState.SUSPECTED_STALLED,
        AttemptState.ORPHANED,
        AttemptState.RECOVERY_PENDING,
    }
)

_TRANSITIONS: dict[AttemptState, frozenset[AttemptState]] = {
    AttemptState.RUNNING: frozenset(
        {
            AttemptState.SUSPECTED_STALLED,
            AttemptState.ORPHANED,
            AttemptState.FAILED,
            AttemptState.COMPLETED,
        }
    ),
    AttemptState.SUSPECTED_STALLED: frozenset(
        {
            # A quiet worker that speaks again is simply running.
            AttemptState.RUNNING,
            AttemptState.ORPHANED,
            AttemptState.RECOVERY_PENDING,
            AttemptState.FAILED,
            AttemptState.COMPLETED,
        }
    ),
    AttemptState.ORPHANED: frozenset({AttemptState.RECOVERY_PENDING}),
    AttemptState.RECOVERY_PENDING: frozenset(
        {AttemptState.RESUMED, AttemptState.REPLACED, AttemptState.FAILED}
    ),
    AttemptState.RESUMED: frozenset(),
    AttemptState.REPLACED: frozenset(),
    AttemptState.FAILED: frozenset(),
    AttemptState.COMPLETED: frozenset(),
}


class FailureClass(StrEnum):
    """Why an attempt ended, which decides what recovery is safe."""

    #: Worker vanished: safe to replace, nothing partial was promised.
    WORKER_LOST = "worker-lost"
    #: Worker stopped reporting but may still hold the worktree.
    WORKER_STALLED = "worker-stalled"
    #: Provider refused: auth, quota or outage. Replacement provider may work.
    PROVIDER_UNAVAILABLE = "provider-unavailable"
    #: The change itself is wrong; retrying the same thing will fail again.
    WORK_REJECTED = "work-rejected"
    #: Local environment problem, repairable before another attempt.
    ENVIRONMENT = "environment"
    #: Operator or policy stopped it.
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


#: Failure classes where trying again, with the same or another worker, is safe.
RETRYABLE_CLASSES = frozenset(
    {
        FailureClass.WORKER_LOST,
        FailureClass.WORKER_STALLED,
        FailureClass.PROVIDER_UNAVAILABLE,
        FailureClass.ENVIRONMENT,
    }
)

#: What reaching a state already tells us about why the attempt ended.
#:
#: Deciding an attempt is orphaned *is* learning the worker vanished, and
#: deciding it is suspected-stalled *is* learning it stopped reporting. Leaving
#: the failure unnamed made recovery read it as UNKNOWN and refuse to retry the
#: very case the contract calls safe to replace, so the state names it.
_IMPLIED_FAILURE: Mapping[AttemptState, FailureClass] = {
    AttemptState.ORPHANED: FailureClass.WORKER_LOST,
    AttemptState.SUSPECTED_STALLED: FailureClass.WORKER_STALLED,
}


class AttemptTransitionError(ValueError):
    """Raised when an attempt is moved somewhere its lifecycle forbids."""


@dataclass(frozen=True)
class AttemptRecord:
    attempt_id: str
    task_id: str
    worker_id: str
    provider: str
    agent: str | None = None
    state: AttemptState = AttemptState.RUNNING
    started_at: str = ""
    heartbeat_at: str | None = None
    #: Distinct from heartbeat on purpose: a process can be alive and stuck.
    last_progress_at: str | None = None
    checkpoint_ref: str | None = None
    worktree: str | None = None
    base_commit: str | None = None
    result_commit: str | None = None
    evidence_refs: tuple[str, ...] = ()
    failure_class: FailureClass | None = None
    exit_code: int | None = None
    finished_at: str | None = None
    pid: int | None = None
    process_start_token: str | None = None
    #: Set when this attempt exists because an earlier one was recovered.
    replaces_attempt_id: str | None = None
    history: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("attempt_id", "task_id", "worker_id", "provider"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"attempt {name} is required")
        if any(char in self.attempt_id for char in "/\\") or self.attempt_id in {".", ".."}:
            raise ValueError("attempt_id must be a file-safe identifier")

    @property
    def open(self) -> bool:
        return self.state in OPEN_STATES

    def transition(
        self,
        state: AttemptState,
        reason: str,
        *,
        at: str,
        failure_class: FailureClass | None = None,
        exit_code: int | None = None,
        #: The commit that now holds the accepted work, when there is one.
        result_commit: str | None = None,
    ) -> AttemptRecord:
        """Move to a new lifecycle state, refusing anything the contract forbids."""
        allowed = _TRANSITIONS[self.state]
        if state not in allowed:
            raise AttemptTransitionError(
                f"attempt cannot move from {self.state.value} to {state.value}"
            )
        entry: dict[str, Any] = {
            "from": self.state.value,
            "to": state.value,
            "at": at,
            "reason": reason,
        }
        named = failure_class or _IMPLIED_FAILURE.get(state)
        if named is not None:
            entry["failure_class"] = named.value
        return replace(
            self,
            state=state,
            failure_class=named or self.failure_class,
            exit_code=self.exit_code if exit_code is None else exit_code,
            result_commit=self.result_commit if result_commit is None else result_commit,
            finished_at=at if state in TERMINAL_STATES else self.finished_at,
            history=(*self.history, entry),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = ATTEMPT_SCHEMA_VERSION
        payload["state"] = self.state.value
        payload["failure_class"] = (
            None if self.failure_class is None else self.failure_class.value
        )
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["history"] = [dict(entry) for entry in self.history]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AttemptRecord:
        failure = payload.get("failure_class")
        return cls(
            attempt_id=str(payload["attempt_id"]),
            task_id=str(payload["task_id"]),
            worker_id=str(payload["worker_id"]),
            provider=str(payload["provider"]),
            agent=payload.get("agent"),
            state=AttemptState(payload.get("state", AttemptState.RUNNING.value)),
            started_at=str(payload.get("started_at", "")),
            heartbeat_at=payload.get("heartbeat_at"),
            last_progress_at=payload.get("last_progress_at"),
            checkpoint_ref=payload.get("checkpoint_ref"),
            worktree=payload.get("worktree"),
            base_commit=payload.get("base_commit"),
            result_commit=payload.get("result_commit"),
            evidence_refs=tuple(payload.get("evidence_refs", ())),
            failure_class=None if failure is None else FailureClass(failure),
            exit_code=payload.get("exit_code"),
            finished_at=payload.get("finished_at"),
            pid=payload.get("pid"),
            process_start_token=payload.get("process_start_token"),
            replaces_attempt_id=payload.get("replaces_attempt_id"),
            history=tuple(dict(entry) for entry in payload.get("history", ())),
        )
