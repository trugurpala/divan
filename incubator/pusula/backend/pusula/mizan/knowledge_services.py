from __future__ import annotations

import uuid
from datetime import datetime

from pusula.domain.knowledge import (
    CapabilityNode,
    CapabilityRelationship,
    ClaimKind,
    ContradictionResolution,
    DataClass,
    EvidenceRef,
    KnowledgeClaim,
    KnowledgeSnapshot,
    Materiality,
    NodeType,
    RelationshipKind,
    SourceRef,
)

from .models import (
    CapabilityGraphNode,
    CapabilityGraphRelationship,
    ContradictionResolutionRecord,
    EvidenceArtifact,
    KnowledgeClaimRecord,
    KnowledgeSource,
)
from .services import MutationResult, record_mutation


def persist_knowledge_snapshot(
    *,
    team_id: uuid.UUID,
    snapshot: KnowledgeSnapshot,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> MutationResult:
    snapshot.validate()
    aggregate_id = uuid.uuid4()

    def mutate_projection() -> None:
        sources: dict[str, KnowledgeSource] = {}
        for row in snapshot.sources:
            sources[row.source_id] = KnowledgeSource.objects.create(
                team_id=team_id,
                source_key=row.source_id,
                locator=row.locator,
                authority=row.authority,
                observed_at=row.observed_at,
                valid_until=row.valid_until,
                content_sha256=row.content_sha256,
            )
        for row in snapshot.evidence:
            EvidenceArtifact.objects.create(
                team_id=team_id,
                evidence_key=row.evidence_id,
                source=sources[row.source_id],
                summary=row.summary,
                captured_at=row.captured_at,
                valid_until=row.valid_until,
                data_class=row.data_class.value,
                retention_days=row.retention_days,
                payload_sha256=row.payload_sha256,
            )
        for row in snapshot.claims:
            KnowledgeClaimRecord.objects.create(
                team_id=team_id,
                claim_key=row.claim_id,
                kind=row.kind.value,
                subject=row.subject,
                predicate=row.predicate,
                value=row.value,
                materiality=row.materiality.value,
                evidence_keys=list(row.evidence_ids),
                contradicts_claim_keys=list(row.contradicts_claim_ids),
            )
        for row in snapshot.contradiction_resolutions:
            ContradictionResolutionRecord.objects.create(
                team_id=team_id,
                resolution_key=row.resolution_id,
                contradiction_claim_key=row.contradiction_claim_id,
                summary=row.summary,
                evidence_keys=list(row.evidence_ids),
            )
        nodes: dict[str, CapabilityGraphNode] = {}
        for row in snapshot.capability_nodes:
            nodes[row.node_id] = CapabilityGraphNode.objects.create(
                team_id=team_id,
                node_key=row.node_id,
                node_type=row.node_type.value,
                name=row.name,
            )
        for row in snapshot.capability_relationships:
            CapabilityGraphRelationship.objects.create(
                team_id=team_id,
                relationship_key=row.relationship_id,
                source_node=nodes[row.source_node_id],
                kind=row.kind.value,
                target_node=nodes[row.target_node_id],
                evidence_keys=list(row.evidence_ids),
            )

    return record_mutation(
        team_id=team_id,
        aggregate_type="knowledge-snapshot",
        aggregate_id=aggregate_id,
        event_type="knowledge.snapshot.recorded",
        event_payload={
            "source_count": len(snapshot.sources),
            "evidence_count": len(snapshot.evidence),
            "claim_count": len(snapshot.claims),
            "resolution_count": len(snapshot.contradiction_resolutions),
            "capability_node_count": len(snapshot.capability_nodes),
            "capability_relationship_count": len(snapshot.capability_relationships),
        },
        topic="mizan.knowledge.snapshot.recorded",
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        mutate_projection=mutate_projection,
    )


def load_knowledge_snapshot(*, team_id: uuid.UUID) -> KnowledgeSnapshot:
    sources = tuple(
        SourceRef(
            source_id=row.source_key,
            locator=row.locator,
            authority=row.authority,
            observed_at=row.observed_at,
            valid_until=row.valid_until,
            content_sha256=row.content_sha256,
        )
        for row in KnowledgeSource.objects.filter(team_id=team_id).order_by(
            "created_at", "source_key"
        )
    )
    evidence = tuple(
        EvidenceRef(
            evidence_id=row.evidence_key,
            source_id=row.source.source_key,
            summary=row.summary,
            captured_at=row.captured_at,
            valid_until=row.valid_until,
            data_class=DataClass(row.data_class),
            retention_days=row.retention_days,
            payload_sha256=row.payload_sha256,
        )
        for row in EvidenceArtifact.objects.filter(team_id=team_id)
        .select_related("source")
        .order_by("created_at", "evidence_key")
    )
    claims = tuple(
        KnowledgeClaim(
            claim_id=row.claim_key,
            kind=ClaimKind(row.kind),
            subject=row.subject,
            predicate=row.predicate,
            value=row.value,
            materiality=Materiality(row.materiality),
            evidence_ids=tuple(row.evidence_keys),
            contradicts_claim_ids=tuple(row.contradicts_claim_keys),
        )
        for row in KnowledgeClaimRecord.objects.filter(team_id=team_id).order_by(
            "created_at", "claim_key"
        )
    )
    nodes = tuple(
        CapabilityNode(
            node_id=row.node_key,
            node_type=NodeType(row.node_type),
            name=row.name,
        )
        for row in CapabilityGraphNode.objects.filter(team_id=team_id).order_by(
            "created_at", "node_key"
        )
    )
    relationships = tuple(
        CapabilityRelationship(
            relationship_id=row.relationship_key,
            source_node_id=row.source_node.node_key,
            kind=RelationshipKind(row.kind),
            target_node_id=row.target_node.node_key,
            evidence_ids=tuple(row.evidence_keys),
        )
        for row in CapabilityGraphRelationship.objects.filter(team_id=team_id)
        .select_related("source_node", "target_node")
        .order_by("created_at", "relationship_key")
    )
    resolutions = tuple(
        ContradictionResolution(
            resolution_id=row.resolution_key,
            contradiction_claim_id=row.contradiction_claim_key,
            summary=row.summary,
            evidence_ids=tuple(row.evidence_keys),
        )
        for row in ContradictionResolutionRecord.objects.filter(team_id=team_id).order_by(
            "created_at", "resolution_key"
        )
    )
    snapshot = KnowledgeSnapshot(
        sources,
        evidence,
        claims,
        nodes,
        relationships,
        resolutions,
    )
    snapshot.validate()
    return snapshot


def critical_decision_blockers(
    *,
    team_id: uuid.UUID,
    at: datetime,
) -> tuple[str, ...]:
    return load_knowledge_snapshot(team_id=team_id).critical_decision_blockers(at=at)
