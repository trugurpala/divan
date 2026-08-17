"""Walk one tool candidate through certification, one proven step at a time.

The stage order is fixed: discover, verify the source, stage the files, test in
isolation, certify against the contract, canary, promote. Only PASS evidence
moves a candidate forward. FAIL rejects it, or rolls back once it is live and
the way back is proven. Everything else, UNKNOWN, SKIPPED, TIMEOUT, BLOCKED or
NOT_INSTALLED, holds: a step that did not run is not a step that passed.

The contract smoke checklist names what certification must observe about a
coding worker before Divan will drive it. Gate states are the ones the quality
factory already uses, so "certified" means the same thing everywhere.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from .quality_factory import GateResult, GateState
from .update_governor import (
    PipelineStage,
    RollbackMechanism,
    ToolStatus,
    ToolVersionRecord,
)

PIPELINE_SCHEMA_VERSION = 1

#: The ordered path a candidate walks. Terminal stages are not on it.
STAGE_ORDER: tuple[PipelineStage, ...] = (
    PipelineStage.DISCOVER,
    PipelineStage.VERIFY_SOURCE,
    PipelineStage.STAGE,
    PipelineStage.ISOLATED_TEST,
    PipelineStage.CERTIFY,
    PipelineStage.CANARY,
    PipelineStage.PROMOTE,
)

#: Stages nothing advances out of. Leaving one is a re-entry, not a step.
TERMINAL_STAGES = frozenset(
    {PipelineStage.HOLD, PipelineStage.REJECT, PipelineStage.ROLLBACK}
)

#: What each stage says about the tool while the candidate sits there.
STAGE_STATUS: dict[PipelineStage, ToolStatus] = {
    PipelineStage.DISCOVER: ToolStatus.CANDIDATE,
    PipelineStage.VERIFY_SOURCE: ToolStatus.CANDIDATE,
    PipelineStage.STAGE: ToolStatus.CANDIDATE,
    PipelineStage.ISOLATED_TEST: ToolStatus.TESTING,
    PipelineStage.CERTIFY: ToolStatus.TESTING,
    PipelineStage.CANARY: ToolStatus.CERTIFIED,
    PipelineStage.PROMOTE: ToolStatus.CERTIFIED,
    PipelineStage.HOLD: ToolStatus.HOLD,
    PipelineStage.REJECT: ToolStatus.REJECTED,
    PipelineStage.ROLLBACK: ToolStatus.DEGRADED,
}

#: Every capability certification has to observe before a worker is driven.
CONTRACT_SMOKE_CHECKS: tuple[str, ...] = (
    "version",
    "auth",
    "headless",
    "cwd",
    "git-worktree",
    "cancel",
    "timeout",
    "diff",
    "evidence",
    "review-mode",
)


@dataclass(frozen=True)
class StageEvidence:
    """What one stage observed. Carries the stage so it cannot be misapplied."""

    stage: PipelineStage
    state: GateState
    detail: str = ""
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if self.state is not GateState.PASS and not self.detail.strip():
            raise ValueError(
                f"{self.stage.value} evidence is {self.state.value} and must say why"
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stage"] = self.stage.value
        payload["state"] = self.state.value
        return payload


@dataclass(frozen=True)
class StageTransition:
    from_stage: PipelineStage
    to_stage: PipelineStage
    reason: str

    @property
    def advanced(self) -> bool:
        return self.to_stage not in TERMINAL_STAGES and self.to_stage is not self.from_stage

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PIPELINE_SCHEMA_VERSION,
            "from_stage": self.from_stage.value,
            "to_stage": self.to_stage.value,
            "advanced": self.advanced,
            "reason": self.reason,
        }


def _in_live_slot(record: ToolVersionRecord) -> bool:
    """True once ``promote`` has moved the candidate into the installed slot.

    Canary runs the candidate beside the current version, so a canary failure
    has nothing to roll back. Only a promoted version can regress.
    """
    return (
        record.stage is PipelineStage.PROMOTE
        and record.status is ToolStatus.CURRENT_CERTIFIED
    )


def _on_failure(record: ToolVersionRecord) -> StageTransition:
    """A failed step rejects a candidate; a failed live version goes back, if it can."""
    stage = record.stage
    if not _in_live_slot(record):
        return StageTransition(
            stage, PipelineStage.REJECT, f"{stage.value} failed before the live slot"
        )
    if record.rollback_mechanism is RollbackMechanism.PROVEN:
        return StageTransition(
            stage, PipelineStage.ROLLBACK, "live version regressed; rolling back to last good"
        )
    return StageTransition(
        stage,
        PipelineStage.HOLD,
        "live version regressed and rollback is "
        f"{record.rollback_mechanism.value}; the owner must act",
    )


def _status_after(
    record: ToolVersionRecord, transition: StageTransition, evidence: StageEvidence
) -> ToolStatus:
    """Status follows stage, except where the truth is more specific."""
    if transition.to_stage is transition.from_stage:
        return record.status
    if (
        transition.to_stage is PipelineStage.HOLD
        and evidence.state is GateState.FAIL
        and _in_live_slot(record)
    ):
        # Nothing moved, but the tool the owner is running is now worse.
        return ToolStatus.DEGRADED
    return STAGE_STATUS[transition.to_stage]


def next_stage(record: ToolVersionRecord, evidence: StageEvidence) -> StageTransition:
    """Decide the next stage from the record and one piece of evidence.

    Deterministic and closed: the same record and evidence always give the same
    answer, and anything short of PASS never moves forward. Evidence for a
    different stage than the record is at is treated as missing, not as a
    shortcut. A terminal stage stays where it is; re-entry is a separate act.
    """
    stage = record.stage
    if stage in TERMINAL_STAGES:
        return StageTransition(stage, stage, "terminal stage; re-entry needs new evidence")
    if evidence.stage is not stage:
        return StageTransition(
            stage,
            PipelineStage.HOLD,
            f"evidence is for {evidence.stage.value} but the record is at {stage.value}",
        )
    if evidence.state is GateState.FAIL:
        return _on_failure(record)
    if evidence.state is not GateState.PASS:
        return StageTransition(
            stage,
            PipelineStage.HOLD,
            f"{stage.value} evidence is {evidence.state.value}, not PASS: {evidence.detail}",
        )
    if stage is PipelineStage.PROMOTE:
        return StageTransition(stage, stage, "promote is the last stage; nothing further")
    following = STAGE_ORDER[STAGE_ORDER.index(stage) + 1]
    return StageTransition(stage, following, f"{stage.value} passed")


def advance(record: ToolVersionRecord, evidence: StageEvidence) -> ToolVersionRecord:
    """Apply ``next_stage`` to the record and keep the evidence on it.

    Status follows stage. A rejection records why. A rollback puts the last
    good version back into the installed slot and keeps the version that
    regressed as the candidate, so it can re-enter on new evidence.
    """
    transition = next_stage(record, evidence)
    trail = record.certification_evidence
    if evidence.evidence_ref:
        trail = (*trail, evidence.evidence_ref)
    changes: dict[str, Any] = {
        "stage": transition.to_stage,
        "status": _status_after(record, transition, evidence),
        "certification_evidence": trail,
    }
    if transition.to_stage in {PipelineStage.REJECT, PipelineStage.ROLLBACK}:
        changes["rejection_reason"] = evidence.detail or transition.reason
    if transition.to_stage is PipelineStage.ROLLBACK:
        changes["installed_version"] = record.last_good_version
        changes["candidate_version"] = record.installed_version
    return replace(record, **changes)


@dataclass(frozen=True)
class CertificationResult:
    """The contract smoke run for one tool version, one gate per check.

    Certified means every check in ``CONTRACT_SMOKE_CHECKS`` was reported and
    every one is PASS. A check that was not reported is missing, and missing
    is not passing.
    """

    tool_id: str
    version: str
    results: tuple[GateResult, ...]

    def __post_init__(self) -> None:
        unknown = sorted({r.name for r in self.results} - set(CONTRACT_SMOKE_CHECKS))
        if unknown:
            raise ValueError("unknown contract smoke check(s): " + ", ".join(unknown))

    @property
    def states(self) -> dict[str, GateState]:
        """Each check's state. A check reported twice keeps its worst outcome."""
        seen: dict[str, GateState] = {}
        for result in self.results:
            current = seen.get(result.name)
            if current is None or (current is GateState.PASS and not result.satisfies):
                seen[result.name] = result.state
        return seen

    @property
    def missing(self) -> tuple[str, ...]:
        states = self.states
        return tuple(name for name in CONTRACT_SMOKE_CHECKS if name not in states)

    @property
    def not_passing(self) -> tuple[str, ...]:
        states = self.states
        return tuple(
            name for name in CONTRACT_SMOKE_CHECKS
            if name in states and states[name] is not GateState.PASS
        )

    @property
    def certified(self) -> bool:
        return not self.missing and not self.not_passing

    def as_evidence(self, *, evidence_ref: str | None = None) -> StageEvidence:
        """Fold the run into one piece of CERTIFY-stage evidence.

        Any FAIL is a FAIL. Otherwise the first non-passing or missing check
        decides, so a skipped check holds rather than fails.
        """
        stage = PipelineStage.CERTIFY
        if self.certified:
            return StageEvidence(stage, GateState.PASS, evidence_ref=evidence_ref)
        states = self.states
        failed = [name for name in self.not_passing if states[name] is GateState.FAIL]
        if failed:
            detail = "contract smoke failed: " + ", ".join(failed)
            return StageEvidence(stage, GateState.FAIL, detail, evidence_ref)
        if self.not_passing:
            first = self.not_passing[0]
            detail = f"contract smoke {first} is {states[first].value}"
            return StageEvidence(stage, states[first], detail, evidence_ref)
        detail = "contract smoke did not report: " + ", ".join(self.missing)
        return StageEvidence(stage, GateState.UNKNOWN, detail, evidence_ref)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PIPELINE_SCHEMA_VERSION,
            "tool_id": self.tool_id,
            "version": self.version,
            "required_checks": list(CONTRACT_SMOKE_CHECKS),
            "results": [item.to_dict() for item in self.results],
            "states": {name: state.value for name, state in self.states.items()},
            "missing": list(self.missing),
            "not_passing": list(self.not_passing),
            "certified": self.certified,
        }


def certification_from_states(
    tool_id: str, version: str, states: Iterable[tuple[str, GateState, str]]
) -> CertificationResult:
    """Build a result from (check, state, reason) triples; a small convenience."""
    results = tuple(
        GateResult(name=name, state=state, reason=reason or None)
        for name, state, reason in states
    )
    return CertificationResult(tool_id=tool_id, version=version, results=results)
