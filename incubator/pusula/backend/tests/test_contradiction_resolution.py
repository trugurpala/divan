from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from pusula.domain.knowledge import ContradictionResolution
from pusula.mizan.contradiction_services import append_contradiction_resolution
from pusula.mizan.knowledge_services import (
    critical_decision_blockers,
    persist_knowledge_snapshot,
)
from pusula.mizan.models import ContradictionResolutionRecord, DomainEvent, KnowledgeClaimRecord
from tests.test_knowledge_persistence import snapshot

NOW = datetime(2026, 8, 24, tzinfo=timezone.utc)


class IncrementalContradictionResolutionTests(TestCase):
    def setUp(self) -> None:
        self.team_id = uuid.uuid4()
        persist_knowledge_snapshot(
            team_id=self.team_id,
            snapshot=snapshot(resolved=False),
            idempotency_key="knowledge-initial",
            correlation_id=uuid.uuid4(),
        )

    def resolution(self, evidence_ids: tuple[str, ...] = ("evidence-1",)) -> ContradictionResolution:
        return ContradictionResolution(
            resolution_id="resolution-later",
            contradiction_claim_id="contradiction-1",
            summary="Later primary evidence resolves the conflict",
            evidence_ids=evidence_ids,
        )

    def test_later_resolution_clears_blocker_without_mutating_claim(self) -> None:
        claim = KnowledgeClaimRecord.objects.get(
            team_id=self.team_id,
            claim_key="contradiction-1",
        )
        original = (
            claim.kind,
            claim.subject,
            claim.predicate,
            claim.value,
            list(claim.evidence_keys),
            list(claim.contradicts_claim_keys),
        )
        self.assertEqual(
            critical_decision_blockers(team_id=self.team_id, at=NOW),
            ("unresolved-contradiction:contradiction-1",),
        )

        result = append_contradiction_resolution(
            team_id=self.team_id,
            resolution=self.resolution(),
            idempotency_key="resolution-later",
            correlation_id=uuid.uuid4(),
        )
        self.assertTrue(result.created)
        self.assertEqual(
            critical_decision_blockers(team_id=self.team_id, at=NOW + timedelta(hours=1)),
            (),
        )
        claim.refresh_from_db()
        self.assertEqual(
            (
                claim.kind,
                claim.subject,
                claim.predicate,
                claim.value,
                list(claim.evidence_keys),
                list(claim.contradicts_claim_keys),
            ),
            original,
        )
        self.assertEqual(ContradictionResolutionRecord.objects.count(), 1)
        self.assertEqual(DomainEvent.objects.count(), 2)

    def test_resolution_is_idempotent(self) -> None:
        first = append_contradiction_resolution(
            team_id=self.team_id,
            resolution=self.resolution(),
            idempotency_key="same-resolution",
            correlation_id=uuid.uuid4(),
        )
        second = append_contradiction_resolution(
            team_id=self.team_id,
            resolution=self.resolution(),
            idempotency_key="same-resolution",
            correlation_id=uuid.uuid4(),
        )
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(ContradictionResolutionRecord.objects.count(), 1)
        self.assertEqual(DomainEvent.objects.count(), 2)

    def test_resolution_rejects_missing_same_team_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "same team"):
            append_contradiction_resolution(
                team_id=self.team_id,
                resolution=self.resolution(("missing-evidence",)),
                idempotency_key="missing-evidence",
                correlation_id=uuid.uuid4(),
            )

    def test_resolution_rejects_non_contradiction_target(self) -> None:
        fact = KnowledgeClaimRecord.objects.get(team_id=self.team_id, claim_key="fact-a")
        resolution = ContradictionResolution(
            resolution_id="bad-target",
            contradiction_claim_id=fact.claim_key,
            summary="Invalid target",
            evidence_ids=("evidence-1",),
        )
        with self.assertRaisesRegex(ValueError, "existing contradiction"):
            append_contradiction_resolution(
                team_id=self.team_id,
                resolution=resolution,
                idempotency_key="bad-target",
                correlation_id=uuid.uuid4(),
            )
