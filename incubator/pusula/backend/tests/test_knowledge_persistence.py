from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from django.test import TestCase
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
    sha256_text,
)
from pusula.mizan.knowledge_services import (
    critical_decision_blockers,
    load_knowledge_snapshot,
    persist_knowledge_snapshot,
)
from pusula.mizan.models import (
    CapabilityGraphNode,
    CapabilityGraphRelationship,
    ContradictionResolutionRecord,
    DomainEvent,
    EvidenceArtifact,
    KnowledgeClaimRecord,
    KnowledgeSource,
    OutboxMessage,
)

NOW = datetime(2026, 8, 24, tzinfo=timezone.utc)


def snapshot(*, resolved: bool = False) -> KnowledgeSnapshot:
    source = SourceRef(
        "source-1",
        "https://example.test/provider",
        "vendor-docs",
        NOW,
        NOW + timedelta(days=30),
        sha256_text("source"),
    )
    evidence = EvidenceRef(
        "evidence-1",
        "source-1",
        "Provider capability page",
        NOW,
        NOW + timedelta(days=30),
        DataClass.PUBLIC,
        None,
        sha256_text("payload"),
    )
    fact_a = KnowledgeClaim(
        "fact-a",
        ClaimKind.FACT,
        "provider-x",
        "supports",
        "canary",
        Materiality.CRITICAL,
        ("evidence-1",),
    )
    fact_b = KnowledgeClaim(
        "fact-b",
        ClaimKind.FACT,
        "provider-x",
        "supports",
        "no-canary",
        Materiality.MEDIUM,
        ("evidence-1",),
    )
    contradiction = KnowledgeClaim(
        "contradiction-1",
        ClaimKind.CONTRADICTION,
        "provider-x",
        "supports",
        "conflicting canary evidence",
        Materiality.HIGH,
        (),
        ("fact-a", "fact-b"),
    )
    resolutions = ()
    if resolved:
        resolutions = (
            ContradictionResolution(
                "resolution-1",
                "contradiction-1",
                "Vendor primary docs resolve the conflict",
                ("evidence-1",),
            ),
        )
    nodes = (
        CapabilityNode("provider-x", NodeType.PROVIDER, "Provider X"),
        CapabilityNode("provider-x-pro", NodeType.EDITION, "Provider X Pro"),
        CapabilityNode("canary", NodeType.CAPABILITY, "Canary"),
    )
    relationships = (
        CapabilityRelationship(
            "rel-edition",
            "provider-x-pro",
            RelationshipKind.EDITION_OF,
            "provider-x",
        ),
        CapabilityRelationship(
            "rel-canary",
            "provider-x-pro",
            RelationshipKind.PROVIDES,
            "canary",
            ("evidence-1",),
        ),
    )
    return KnowledgeSnapshot(
        (source,),
        (evidence,),
        (fact_a, fact_b, contradiction),
        nodes,
        relationships,
        resolutions,
    )


class KnowledgePersistenceTests(TestCase):
    def setUp(self) -> None:
        self.team_id = uuid.uuid4()

    def persist(self, *, key: str = "knowledge-1", resolved: bool = False):
        return persist_knowledge_snapshot(
            team_id=self.team_id,
            snapshot=snapshot(resolved=resolved),
            idempotency_key=key,
            correlation_id=uuid.uuid4(),
        )

    def test_persists_graph_with_event_and_outbox(self) -> None:
        result = self.persist()
        self.assertTrue(result.created)
        self.assertEqual(KnowledgeSource.objects.count(), 1)
        self.assertEqual(EvidenceArtifact.objects.count(), 1)
        self.assertEqual(KnowledgeClaimRecord.objects.count(), 3)
        self.assertEqual(CapabilityGraphNode.objects.count(), 3)
        self.assertEqual(CapabilityGraphRelationship.objects.count(), 2)
        self.assertEqual(DomainEvent.objects.count(), 1)
        self.assertEqual(OutboxMessage.objects.count(), 1)

    def test_duplicate_idempotency_does_not_duplicate_graph(self) -> None:
        first = self.persist(key="same-key")
        second = self.persist(key="same-key")
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(KnowledgeSource.objects.count(), 1)
        self.assertEqual(KnowledgeClaimRecord.objects.count(), 3)
        self.assertEqual(DomainEvent.objects.count(), 1)

    def test_load_reconstructs_provider_edition_capability_graph(self) -> None:
        self.persist()
        loaded = load_knowledge_snapshot(team_id=self.team_id)
        self.assertEqual(len(loaded.sources), 1)
        self.assertEqual(len(loaded.evidence), 1)
        self.assertEqual(len(loaded.claims), 3)
        self.assertEqual(len(loaded.capability_nodes), 3)
        self.assertEqual(len(loaded.capability_relationships), 2)

    def test_unresolved_material_contradiction_blocks_from_database(self) -> None:
        self.persist()
        self.assertEqual(
            critical_decision_blockers(team_id=self.team_id, at=NOW),
            ("unresolved-contradiction:contradiction-1",),
        )

    def test_resolution_is_append_only_and_clears_blocker(self) -> None:
        self.persist(resolved=True)
        self.assertEqual(ContradictionResolutionRecord.objects.count(), 1)
        self.assertEqual(critical_decision_blockers(team_id=self.team_id, at=NOW), ())
        resolution = ContradictionResolutionRecord.objects.get()
        resolution.summary = "mutated"
        with self.assertRaisesRegex(TypeError, "append-only"):
            resolution.save()

    def test_other_team_cannot_observe_knowledge_graph(self) -> None:
        self.persist()
        other = load_knowledge_snapshot(team_id=uuid.uuid4())
        self.assertEqual(other.sources, ())
        self.assertEqual(other.evidence, ())
        self.assertEqual(other.claims, ())

    def test_source_and_evidence_are_append_only(self) -> None:
        self.persist()
        source_row = KnowledgeSource.objects.get()
        source_row.authority = "mutated"
        with self.assertRaisesRegex(TypeError, "append-only"):
            source_row.save()
        evidence_row = EvidenceArtifact.objects.get()
        with self.assertRaisesRegex(TypeError, "append-only"):
            evidence_row.delete()
