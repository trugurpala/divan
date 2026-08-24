from __future__ import annotations

import uuid

from pusula.domain.knowledge import ClaimKind, ContradictionResolution

from .models import ContradictionResolutionRecord, EvidenceArtifact, KnowledgeClaimRecord
from .services import MutationResult, record_mutation


def append_contradiction_resolution(
    *,
    team_id: uuid.UUID,
    resolution: ContradictionResolution,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> MutationResult:
    resolution.validate()
    claim = KnowledgeClaimRecord.objects.filter(
        team_id=team_id,
        claim_key=resolution.contradiction_claim_id,
    ).first()
    if claim is None or ClaimKind(claim.kind) is not ClaimKind.CONTRADICTION:
        raise ValueError("resolution target must be an existing contradiction")

    available_evidence = set(
        EvidenceArtifact.objects.filter(
            team_id=team_id,
            evidence_key__in=resolution.evidence_ids,
        ).values_list("evidence_key", flat=True)
    )
    missing = sorted(set(resolution.evidence_ids) - available_evidence)
    if missing:
        raise ValueError("resolution evidence must already exist for the same team")

    def mutate_projection() -> None:
        ContradictionResolutionRecord.objects.create(
            team_id=team_id,
            resolution_key=resolution.resolution_id,
            contradiction_claim_key=resolution.contradiction_claim_id,
            summary=resolution.summary,
            evidence_keys=list(resolution.evidence_ids),
        )

    return record_mutation(
        team_id=team_id,
        aggregate_type="knowledge-contradiction",
        aggregate_id=claim.id,
        event_type="knowledge.contradiction.resolved",
        event_payload={
            "resolution_key": resolution.resolution_id,
            "contradiction_claim_key": resolution.contradiction_claim_id,
        },
        topic="mizan.knowledge.contradiction.resolved",
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        mutate_projection=mutate_projection,
    )
