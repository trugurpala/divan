"""Draw one bounded lesson candidate from a real failure, not only from a merge.

Task-close learning (task_learning) remembers the one moment Divan holds both
halves of a lesson: what review rejected and what finally merged. Most of what
an agency learns the hard way never merges. An attempt whose change was
rejected outright, a worker that vanished, an attempt that had to be
replaced, a review that came back RETRY, a security gate that failed: each is
a real outcome, and each is worth one short note in memory.

Three limits keep this from becoming a second memory or a source of noise:

* Bounded. A candidate carries identifiers, a failure class and one short
  redacted summary (``SUMMARY_LIMIT`` characters). It never carries stdout,
  stderr, prompts, secrets, worktrees or absolute paths; every free-text
  field goes through ``knowledge_capture.bounded_text``, the same
  collapse-redact-bound rule the capture path already applies.
* Once per task and cause. ``should_record`` refuses a second candidate for
  the same ``(source, task_id, failure_class)``, so a retry loop writes one
  lesson, not one per iteration.
* Candidates only. Everything written here has status ``candidate`` and goes
  through the existing capture path (``lesson_from_failure`` then
  ``KnowledgeStore.upsert``). ``KnowledgeStore.curate`` is the promotion
  authority and is never called from this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable

from .attempt_contract import AttemptRecord, AttemptState, FailureClass
from .knowledge_capture import bounded_text, lesson_from_failure
from .knowledge_contract import KnowledgeItem, KnowledgeStatus
from .knowledge_store import KnowledgeStore

FAILURE_LESSON_SCHEMA_VERSION = 1

#: Upper bound on one candidate's summary. Long enough for a few review
#: findings or history reasons, short enough that a lesson stays a lesson and
#: never becomes a log.
SUMMARY_LIMIT = 240

#: Upper bound on one identifier-like label (worker, provider, reviewer, gate).
LABEL_LIMIT = 80

#: The resolution half a failure candidate honestly does not have yet. Task
#: close learning owns the "what finally passed" half; a failure candidate only
#: says what went wrong, and says so.
UNRESOLVED = "No resolution observed yet; recorded from a real failure as a candidate."

#: Gates whose failure is a security finding rather than a quality one. These
#: are the security gates quality_factory's profiles require; a name that
#: says "security" is accepted too, so a custom gate is not silently ignored.
SECURITY_GATES = frozenset({"authz-negative", "secret-scan", "dependency-scan", "sast"})


class FailureSource(StrEnum):
    """Which real outcome a lesson candidate was drawn from."""

    #: An attempt ended FAILED with the change itself judged wrong.
    WORK_REJECTED = "work-rejected"
    #: The worker process was provably gone before the attempt finished.
    ORPHANED = "orphaned"
    #: Recovery decided a fresh attempt had to take over.
    REPLACED = "replaced"
    #: An independent review came back RETRY.
    REVIEW_FAILURE = "review-failure"
    #: A security gate ran and reported FAIL.
    SECURITY_FAILURE = "security-failure"


#: How an attempt's terminal-or-decided state maps to a lesson source. FAILED
#: is only a lesson when the change itself was rejected; a provider outage or
#: an operator cancel teaches nothing about the work.
_ATTEMPT_SOURCES: dict[AttemptState, FailureSource] = {
    AttemptState.ORPHANED: FailureSource.ORPHANED,
    AttemptState.REPLACED: FailureSource.REPLACED,
}


@dataclass(frozen=True)
class LessonCandidate:
    """One bounded, redacted note drawn from a real failure.

    ``status`` is fixed to ``candidate``: this record is an input to curation,
    never a curated claim. Construction with any other status is refused so
    a candidate cannot be minted already promoted.
    """

    source: FailureSource
    task_id: str
    summary: str
    observed_at: str
    failure_class: FailureClass | None = None
    attempt_id: str | None = None
    worker: str | None = None
    provider: str | None = None
    status: str = KnowledgeStatus.CANDIDATE.value

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("lesson candidate task_id is required")
        if not self.summary.strip():
            raise ValueError("lesson candidate summary is required")
        if len(self.summary) > SUMMARY_LIMIT:
            raise ValueError(f"lesson candidate summary exceeds {SUMMARY_LIMIT} characters")
        if self.status != KnowledgeStatus.CANDIDATE.value:
            raise ValueError("a lesson candidate is always status candidate")

    @property
    def dedupe_key(self) -> tuple[str, str, str | None]:
        """The identity ``should_record`` refuses to record twice for one task."""
        failure = None if self.failure_class is None else self.failure_class.value
        return (self.source.value, self.task_id, failure)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = FAILURE_LESSON_SCHEMA_VERSION
        payload["source"] = self.source.value
        payload["failure_class"] = (
            None if self.failure_class is None else self.failure_class.value
        )
        return payload


def lesson_from_attempt(
    record: AttemptRecord, *, observed_at: str | None = None
) -> LessonCandidate | None:
    """Draw a candidate from an attempt that ended in a real failure.

    Only three outcomes qualify: FAILED with ``WORK_REJECTED``, ORPHANED and
    REPLACED. COMPLETED and RESUMED are not failures; RUNNING,
    SUSPECTED_STALLED and RECOVERY_PENDING are not yet decided; a FAILED
    attempt whose class is a provider outage, an environment fault or a cancel
    says nothing about the work. All of those return ``None``.

    The summary is built from the attempt's history reasons and nothing else.
    Worktree, checkpoint, evidence refs, pid and exit output are deliberately
    left behind: they are where paths and secrets live.
    """
    source = _attempt_source(record)
    if source is None:
        return None
    reasons = [
        str(entry.get("reason", "")).strip()
        for entry in record.history
        if str(entry.get("reason", "")).strip()
    ]
    failure = record.failure_class
    label = failure.value if failure is not None else source.value
    head = f"Attempt ended {record.state.value} ({label})"
    body = "; ".join(reasons) or "no reason recorded"
    return LessonCandidate(
        source=source,
        task_id=record.task_id,
        attempt_id=record.attempt_id,
        worker=bounded_text(record.worker_id, limit=LABEL_LIMIT) or None,
        provider=bounded_text(record.provider, limit=LABEL_LIMIT) or None,
        failure_class=failure,
        summary=_summary(head, body),
        observed_at=observed_at or record.finished_at or _now(),
    )


def lesson_from_review(
    task_id: str,
    verdict: str,
    findings_summary: str,
    reviewer: str,
    *,
    observed_at: str | None = None,
) -> LessonCandidate | None:
    """Draw a candidate from an independent review that returned RETRY.

    PASS teaches nothing worth storing and BLOCKED means the review did not
    happen, so both return ``None``. A RETRY is, by the attempt contract's own
    definition, ``WORK_REJECTED``: the change itself needs to change.
    """
    if str(verdict).strip().casefold() != "retry":
        return None
    who = bounded_text(reviewer, limit=LABEL_LIMIT) or "unnamed reviewer"
    head = f"Review by {who} returned RETRY"
    body = findings_summary.strip() or "no findings recorded"
    return LessonCandidate(
        source=FailureSource.REVIEW_FAILURE,
        task_id=task_id,
        failure_class=FailureClass.WORK_REJECTED,
        summary=_summary(head, body),
        observed_at=observed_at or _now(),
    )


def lesson_from_gate(
    task_id: str,
    gate_name: str,
    state: str,
    reason: str,
    *,
    observed_at: str | None = None,
) -> LessonCandidate | None:
    """Draw a candidate from a security gate that ran and reported FAIL.

    PASS is not a lesson. BLOCKED, TIMEOUT, NOT_INSTALLED, SKIPPED and UNKNOWN
    fail closed for release purposes but describe the gate, not the work, so
    they return ``None`` too. A failing gate outside ``SECURITY_GATES`` (and
    not named "security") is a quality failure that belongs to review
    learning, not here.

    The gate name lives in the summary, not in the dedupe key, so under
    ``should_record`` a task carries one security lesson however many of its
    security gates failed.
    """
    name = bounded_text(gate_name, limit=LABEL_LIMIT)
    if str(state).strip().casefold() != "fail" or not is_security_gate(name):
        return None
    head = f"Security gate {name} failed"
    body = reason.strip() or "no reason recorded"
    return LessonCandidate(
        source=FailureSource.SECURITY_FAILURE,
        task_id=task_id,
        failure_class=FailureClass.WORK_REJECTED,
        summary=_summary(head, body),
        observed_at=observed_at or _now(),
    )


def is_security_gate(gate_name: str) -> bool:
    """True for the profile security gates and anything named as security."""
    name = gate_name.strip().casefold()
    return name in SECURITY_GATES or "security" in name


def should_record(candidate: LessonCandidate, recent: Iterable[LessonCandidate]) -> bool:
    """Decide whether one candidate is new enough to be worth writing.

    Noise threshold: at most one candidate per ``(source, task_id,
    failure_class)``. A task that loops through review RETRY five times, or an
    attempt that is orphaned and replaced under the same class three times,
    yields one lesson for that source, not five. Different sources for the
    same task are still distinct: an orphaned worker and a rejected change are
    two facts, not one repeated.

    ``recent`` is whatever the caller already recorded for the task; the
    module keeps no state of its own.
    """
    key = candidate.dedupe_key
    return all(previous.dedupe_key != key for previous in recent)


def record_candidate(candidate: LessonCandidate, store: KnowledgeStore) -> KnowledgeItem:
    """Write one candidate through the existing capture path, as a candidate.

    The candidate becomes a LESSON item via ``lesson_from_failure`` and is
    stored with ``KnowledgeStore.upsert``, which never touches curation
    columns. This function does not call ``KnowledgeStore.curate`` and there
    is no promotion step here: the item stays ``candidate`` until a human or a
    verification pass decides otherwise.
    """
    item = to_knowledge_item(candidate)
    store.upsert(item)
    return item


def to_knowledge_item(candidate: LessonCandidate) -> KnowledgeItem:
    """Shape a candidate as the LESSON the capture path already knows."""
    failure = candidate.failure_class
    tags = (
        "failure-source:" + candidate.source.value,
        *(() if failure is None else (failure.value,)),
        *(() if candidate.provider is None else (candidate.provider,)),
    )
    return lesson_from_failure(
        problem=f"{candidate.source.value} in task {candidate.task_id}: {candidate.summary}",
        solution=UNRESOLVED,
        tags=tags,
        observed_at=candidate.observed_at,
    )


def _attempt_source(record: AttemptRecord) -> FailureSource | None:
    if record.state is AttemptState.FAILED:
        if record.failure_class is FailureClass.WORK_REJECTED:
            return FailureSource.WORK_REJECTED
        return None
    return _ATTEMPT_SOURCES.get(record.state)


def _summary(head: str, body: str) -> str:
    """Redact, then bound, one summary. Redaction runs first, so a secret or a
    path can never survive by sitting on the truncation boundary."""
    return bounded_text(f"{head}: {body}", limit=SUMMARY_LIMIT)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
