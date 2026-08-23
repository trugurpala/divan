from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Callable, Iterable, TypeVar


class ClaimKind(StrEnum):
    FACT = "fact"
    ASSUMPTION = "assumption"
    UNCERTAINTY = "uncertainty"
    CONTRADICTION = "contradiction"


class Materiality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: str
    locator: str
    authority: str
    observed_at: datetime
    valid_until: datetime | None
    content_sha256: str

    def validate(self) -> None:
        _require_text(self.source_id, "source_id")
        _require_text(self.locator, "source locator")
        _require_text(self.authority, "source authority")
        _validate_aware(self.observed_at)
        _validate_window(self.observed_at, self.valid_until)
        _validate_sha256(self.content_sha256)

    def fresh_at(self, at: datetime) -> bool:
        self.validate()
        _validate_aware(at)
        return self.valid_until is None or at <= self.valid_until


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    source_id: str
    summary: str
    captured_at: datetime
    valid_until: datetime | None
    data_class: DataClass
    retention_days: int | None
    payload_sha256: str

    def validate(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.source_id, "source_id")
        _require_text(self.summary, "evidence summary")
        _validate_aware(self.captured_at)
        _validate_window(self.captured_at, self.valid_until)
        if self.retention_days is not None and self.retention_days < 1:
            raise ValueError("retention_days must be positive")
        if self.data_class is DataClass.RESTRICTED and self.retention_days is None:
            raise ValueError("restricted evidence requires an explicit retention period")
        _validate_sha256(self.payload_sha256)
        _reject_secret_like_summary(self.summary)

    def fresh_at(self, at: datetime) -> bool:
        self.validate()
        _validate_aware(at)
        return self.valid_until is None or at <= self.valid_until


@dataclass(frozen=True, slots=True)
class KnowledgeClaim:
    claim_id: str
    kind: ClaimKind
    subject: str
    predicate: str
    value: str
    materiality: Materiality
    evidence_ids: tuple[str, ...] = ()
    contradicts_claim_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.subject, "subject")
        _require_text(self.predicate, "predicate")
        _require_text(self.value, "value")
        if self.kind is ClaimKind.FACT and not self.evidence_ids:
            raise ValueError("fact requires evidence")
        if self.kind is ClaimKind.CONTRADICTION:
            if len(self.contradicts_claim_ids) < 2:
                raise ValueError("contradiction must reference at least two claims")
        elif self.contradicts_claim_ids:
            raise ValueError("only contradiction records may reference contradicted claims")


@dataclass(frozen=True, slots=True)
class ContradictionResolution:
    resolution_id: str
    contradiction_claim_id: str
    summary: str
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        _require_text(self.resolution_id, "resolution_id")
        _require_text(self.contradiction_claim_id, "contradiction_claim_id")
        _require_text(self.summary, "resolution summary")
        if not self.evidence_ids:
            raise ValueError("contradiction resolution requires evidence")


class NodeType(StrEnum):
    PROVIDER = "provider"
    EDITION = "edition"
    CAPABILITY = "capability"


@dataclass(frozen=True, slots=True)
class CapabilityNode:
    node_id: str
    node_type: NodeType
    name: str

    def validate(self) -> None:
        _require_text(self.node_id, "node_id")
        _require_text(self.name, "node name")


class RelationshipKind(StrEnum):
    PROVIDES = "provides"
    EDITION_OF = "edition-of"
    REQUIRES = "requires"


@dataclass(frozen=True, slots=True)
class CapabilityRelationship:
    relationship_id: str
    source_node_id: str
    kind: RelationshipKind
    target_node_id: str
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        _require_text(self.relationship_id, "relationship_id")
        _require_text(self.source_node_id, "source_node_id")
        _require_text(self.target_node_id, "target_node_id")


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    sources: tuple[SourceRef, ...]
    evidence: tuple[EvidenceRef, ...]
    claims: tuple[KnowledgeClaim, ...]
    capability_nodes: tuple[CapabilityNode, ...] = ()
    capability_relationships: tuple[CapabilityRelationship, ...] = ()
    contradiction_resolutions: tuple[ContradictionResolution, ...] = ()

    def validate(self) -> None:
        source_by_id = _unique_by_id(self.sources, lambda row: row.source_id, "source")
        evidence_by_id = _unique_by_id(self.evidence, lambda row: row.evidence_id, "evidence")
        claim_by_id = _unique_by_id(self.claims, lambda row: row.claim_id, "claim")
        node_by_id = _unique_by_id(
            self.capability_nodes,
            lambda row: row.node_id,
            "capability node",
        )
        _unique_by_id(
            self.capability_relationships,
            lambda row: row.relationship_id,
            "capability relationship",
        )
        _unique_by_id(
            self.contradiction_resolutions,
            lambda row: row.resolution_id,
            "contradiction resolution",
        )
        for row in self.sources:
            row.validate()
        for row in self.evidence:
            row.validate()
            if row.source_id not in source_by_id:
                raise ValueError("evidence references an unknown source")
        for row in self.claims:
            row.validate()
            for evidence_id in row.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise ValueError("claim references unknown evidence")
            for claim_id in row.contradicts_claim_ids:
                if claim_id not in claim_by_id:
                    raise ValueError("contradiction references unknown claim")
        for row in self.contradiction_resolutions:
            row.validate()
            claim = claim_by_id.get(row.contradiction_claim_id)
            if claim is None or claim.kind is not ClaimKind.CONTRADICTION:
                raise ValueError("resolution references unknown contradiction")
            for evidence_id in row.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise ValueError("resolution references unknown evidence")
        for row in self.capability_nodes:
            row.validate()
        for row in self.capability_relationships:
            row.validate()
            if row.source_node_id not in node_by_id or row.target_node_id not in node_by_id:
                raise ValueError("relationship references unknown capability node")
            for evidence_id in row.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise ValueError("relationship references unknown evidence")

    def critical_decision_blockers(self, *, at: datetime) -> tuple[str, ...]:
        self.validate()
        _validate_aware(at)
        source_by_id = {row.source_id: row for row in self.sources}
        evidence_by_id = {row.evidence_id: row for row in self.evidence}
        resolved_contradictions = {
            row.contradiction_claim_id for row in self.contradiction_resolutions
        }
        blockers: list[str] = []
        for claim in self.claims:
            if (
                claim.kind is ClaimKind.CONTRADICTION
                and claim.claim_id not in resolved_contradictions
                and claim.materiality in {Materiality.HIGH, Materiality.CRITICAL}
            ):
                blockers.append(f"unresolved-contradiction:{claim.claim_id}")
            if claim.kind is ClaimKind.FACT and claim.materiality is Materiality.CRITICAL:
                for evidence_id in claim.evidence_ids:
                    evidence = evidence_by_id[evidence_id]
                    source = source_by_id[evidence.source_id]
                    if not evidence.fresh_at(at):
                        blockers.append(f"stale-critical-evidence:{claim.claim_id}:{evidence_id}")
                    if not source.fresh_at(at):
                        blockers.append(
                            f"stale-critical-source:{claim.claim_id}:{source.source_id}"
                        )
        return tuple(sorted(set(blockers)))


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} is required")


def _validate_sha256(value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.casefold()):
        raise ValueError("expected a 64-character sha256 digest")


def _validate_aware(value: datetime) -> None:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")


def _validate_window(start: datetime, end: datetime | None) -> None:
    _validate_aware(start)
    if end is not None:
        _validate_aware(end)
        if end < start:
            raise ValueError("valid_until cannot precede the observation time")


_Row = TypeVar("_Row")


def _unique_by_id(
    rows: Iterable[_Row],
    getter: Callable[[_Row], str],
    label: str,
) -> dict[str, _Row]:
    result: dict[str, _Row] = {}
    for row in rows:
        key = getter(row)
        if key in result:
            raise ValueError(f"duplicate {label} id")
        result[key] = row
    return result


_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key|password)\s*[:=]"
)


def _reject_secret_like_summary(summary: str) -> None:
    if _SECRET_PATTERN.search(summary):
        raise ValueError("evidence summaries must not contain raw secret material")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
