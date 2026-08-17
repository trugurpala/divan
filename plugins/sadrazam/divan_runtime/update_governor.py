"""Govern updates of the managed tools Divan depends on, without ever trusting "latest".

The Cephanelik (armoury) is the set of external tools an agency runs on: codex,
claude, playwright and its chromium. A newer version of any of them is a
candidate, not an upgrade. It earns the live slot only by passing the same
certification the current version passed, and it is promoted only when nothing
is running on the old one and the way back is proven.

This module holds the model and the policy: what a version record says about
itself, which update mode the owner chose, what promotion requires, and the
bounded lesson the governor may hand to memory. The stage machine and the
certification contract live in ``update_pipeline``. Nothing here installs,
downloads or removes anything.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Any, Mapping

GOVERNOR_SCHEMA_VERSION = 1

#: The tools this governor manages. A record for anything else is still valid
#: data; the list says which ones the doctor and the desktop will ask about.
MANAGED_TOOLS: tuple[str, ...] = ("codex", "claude", "playwright", "chromium")


class ToolStatus(StrEnum):
    #: The version in the live slot, and it passed certification there.
    CURRENT_CERTIFIED = "current-certified"
    #: A newer version was seen. Nothing has been proven about it.
    CANDIDATE = "candidate"
    TESTING = "testing"
    #: Passed certification in isolation; not yet in the live slot.
    CERTIFIED = "certified"
    #: Stopped on purpose: evidence was missing, stale or an owner gate is open.
    HOLD = "hold"
    REJECTED = "rejected"
    #: The live version works, but less than it did.
    DEGRADED = "degraded"
    #: Absent from this machine.
    OFFLINE = "offline"
    #: Present, but the wrong shape or version to be used safely.
    INCOMPATIBLE = "incompatible"


class UpdateMode(StrEnum):
    #: Test automatically, then ask the owner before anything is promoted.
    CONTROLLED = "controlled"
    #: Test automatically; promote alone only when the update is contract
    #: compatible, secure and reversible. The default.
    BALANCED = "balanced"
    #: Technical updates happen without asking. The owner gates in
    #: ``HARD_OWNER_GATES`` still hold; no mode can lower them.
    FULL_AUTO = "full-auto"


DEFAULT_MODE = UpdateMode.BALANCED

#: Outcomes a version may come back from. There is no permanent blacklist.
REENTRANT_STATUSES = frozenset(
    {ToolStatus.REJECTED, ToolStatus.HOLD, ToolStatus.DEGRADED}
)


class RollbackMechanism(StrEnum):
    #: A rollback to ``last_good_version`` was executed and verified.
    PROVEN = "proven"
    #: The tool's distribution offers no rollback Divan can drive.
    UNSUPPORTED = "unsupported"
    #: Nobody has tried. Never treated as proven.
    UNTESTED = "untested"


class PipelineStage(StrEnum):
    DISCOVER = "discover"
    VERIFY_SOURCE = "verify-source"
    STAGE = "stage"
    ISOLATED_TEST = "isolated-test"
    CERTIFY = "certify"
    CANARY = "canary"
    #: The candidate is eligible for the live slot; ``promote`` moves it in.
    PROMOTE = "promote"
    HOLD = "hold"
    REJECT = "reject"
    ROLLBACK = "rollback"


#: Decisions the owner alone may take. No update mode, however automatic,
#: lets the governor pass one of these on its own.
HARD_OWNER_GATES: tuple[str, ...] = (
    "credentials",
    "paid-purchase",
    "security-weakening",
    "public-release",
    "production",
)


@dataclass(frozen=True)
class ToolVersionRecord:
    tool_id: str
    installed_version: str | None
    candidate_version: str | None
    #: Where the candidate came from: registry, channel, checksum, as observed.
    source: str
    discovered_at: str
    status: ToolStatus = ToolStatus.CANDIDATE
    stage: PipelineStage = PipelineStage.DISCOVER
    capabilities: tuple[str, ...] = ()
    #: References to the evidence behind the current status, never the claim alone.
    certification_evidence: tuple[str, ...] = ()
    last_good_version: str | None = None
    rejection_reason: str | None = None
    #: Rollback is a claim about the past, so it defaults to "nobody tried".
    rollback_mechanism: RollbackMechanism = RollbackMechanism.UNTESTED
    host: str = ""

    def __post_init__(self) -> None:
        if not self.tool_id.strip():
            raise ValueError("tool_id is required")
        if not self.source.strip():
            raise ValueError(f"tool {self.tool_id} needs a source; provenance is not optional")
        if self.status is ToolStatus.REJECTED and not self.rejection_reason:
            raise ValueError(f"tool {self.tool_id} is rejected and must say why")

    @property
    def rollback_proven(self) -> bool:
        return self.rollback_mechanism is RollbackMechanism.PROVEN

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = GOVERNOR_SCHEMA_VERSION
        payload["status"] = self.status.value
        payload["stage"] = self.stage.value
        payload["rollback_mechanism"] = self.rollback_mechanism.value
        payload["rollback_proven"] = self.rollback_proven
        payload["capabilities"] = list(self.capabilities)
        payload["certification_evidence"] = list(self.certification_evidence)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ToolVersionRecord:
        version = payload.get("schema_version", GOVERNOR_SCHEMA_VERSION)
        if version != GOVERNOR_SCHEMA_VERSION:
            raise ValueError(f"unsupported tool version record schema {version!r}")
        return cls(
            tool_id=str(payload["tool_id"]),
            installed_version=payload.get("installed_version"),
            candidate_version=payload.get("candidate_version"),
            source=str(payload["source"]),
            discovered_at=str(payload.get("discovered_at", "")),
            status=ToolStatus(payload.get("status", ToolStatus.CANDIDATE.value)),
            stage=PipelineStage(payload.get("stage", PipelineStage.DISCOVER.value)),
            capabilities=tuple(payload.get("capabilities", ())),
            certification_evidence=tuple(payload.get("certification_evidence", ())),
            last_good_version=payload.get("last_good_version"),
            rejection_reason=payload.get("rejection_reason"),
            # An absent field means untested. It never means proven.
            rollback_mechanism=RollbackMechanism(
                payload.get("rollback_mechanism", RollbackMechanism.UNTESTED.value)
            ),
            host=str(payload.get("host", "")),
        )


def promotion_decision(
    record: ToolVersionRecord,
    mode: UpdateMode,
    *,
    active_attempts: int,
    contract_smoke_passed: bool,
    security_ok: bool,
    rollback_proven: bool,
) -> tuple[str, str]:
    """Say whether this candidate may take the live slot now, and why.

    Returns ``("promote", reason)`` or ``("hold", reason)``. The order matters:
    a running attempt stops everything, then the owner's mode, then the three
    technical facts. Rollback counts as proven only when the caller observed
    it and the record already carries the proof; a flag alone is a claim.
    """
    if active_attempts > 0:
        return (
            "hold",
            f"{active_attempts} attempt(s) still running on {record.tool_id}; "
            "staged and waiting for idle",
        )
    if record.candidate_version is None:
        return ("hold", f"{record.tool_id} has no candidate version to promote")
    if record.stage is not PipelineStage.PROMOTE:
        return (
            "hold",
            f"{record.tool_id} is at stage {record.stage.value}; "
            "the pipeline has not reached promote",
        )
    if mode is UpdateMode.CONTROLLED:
        return ("hold", "controlled mode never promotes on its own; the owner decides")
    if not contract_smoke_passed:
        return ("hold", "contract smoke did not pass; the candidate is not compatible")
    if not security_ok:
        return ("hold", "security check did not pass; the candidate is not secure")
    if not rollback_proven or not record.rollback_proven:
        return (
            "hold",
            "rollback is not proven "
            f"(record says {record.rollback_mechanism.value}); not reversible",
        )
    if mode is UpdateMode.FULL_AUTO:
        return (
            "promote",
            "full-auto: technical gates passed; owner gates still held: "
            + ", ".join(HARD_OWNER_GATES),
        )
    return ("promote", "balanced: contract compatible, secure and reversible")


def promote(record: ToolVersionRecord) -> ToolVersionRecord:
    """Move the candidate into the live slot, remembering what it replaced.

    Only the record changes. Callers act on the machine after
    ``promotion_decision`` returned ``promote``, never before.
    """
    if record.stage is not PipelineStage.PROMOTE or record.candidate_version is None:
        raise ValueError(f"{record.tool_id} is not at the promote stage with a candidate")
    return replace(
        record,
        installed_version=record.candidate_version,
        candidate_version=None,
        last_good_version=record.installed_version,
        status=ToolStatus.CURRENT_CERTIFIED,
    )


def reenter_candidate(
    record: ToolVersionRecord, *, evidence_ref: str, discovered_at: str
) -> ToolVersionRecord:
    """Let a rejected or held version try again on new evidence.

    There is no permanent blacklist. A rejection was true about one run;
    new evidence starts a new run from discovery, and the old reason is kept
    in the evidence trail rather than forgotten.
    """
    if record.status not in REENTRANT_STATUSES:
        raise ValueError(
            f"{record.tool_id} is {record.status.value}; only rejected, held or rolled-back re-enter"
        )
    if not evidence_ref.strip():
        raise ValueError("re-entry needs new evidence; a retry without it is the same run")
    trail = record.certification_evidence
    if record.rejection_reason:
        trail = (*trail, f"previous rejection: {record.rejection_reason}")
    return replace(
        record,
        status=ToolStatus.CANDIDATE,
        stage=PipelineStage.DISCOVER,
        discovered_at=discovered_at,
        rejection_reason=None,
        certification_evidence=(*trail, evidence_ref),
    )


class LessonOutcome(StrEnum):
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled-back"
    HELD = "held"


@dataclass(frozen=True)
class LessonCandidate:
    """What the governor may tell memory about one version on one host.

    Memory observes; live certification decides. A lesson never authorises a
    promotion, never skips a stage and never blacklists a version. It only
    lets the next run start with better questions.
    """

    tool_id: str
    version: str
    host: str
    outcome: LessonOutcome
    detail: str

    #: Stated on the type so no reader has to infer it.
    AUTHORIZES_PROMOTION = False

    def __post_init__(self) -> None:
        for name in ("tool_id", "version", "detail"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"lesson {name} is required")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = GOVERNOR_SCHEMA_VERSION
        payload["outcome"] = self.outcome.value
        payload["authorizes_promotion"] = self.AUTHORIZES_PROMOTION
        return payload
