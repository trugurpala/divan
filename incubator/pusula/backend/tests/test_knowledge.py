from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from pusula.domain.knowledge import (
    CapabilityNode,
    CapabilityRelationship,
    ClaimKind,
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

NOW = datetime(2026, 8, 24, tzinfo=timezone.utc)


def source(*, valid_for_days: int | None = 1) -> SourceRef:
    return SourceRef(
        source_id="source-1",
        locator="https://example.test/source",
        authority="vendor-docs",
        observed_at=NOW,
        valid_until=None if valid_for_days is None else NOW + timedelta(days=valid_for_days),
        content_sha256=sha256_text("source"),
    )


def evidence(*, valid_for_days: int | None = 1) -> EvidenceRef:
    return EvidenceRef(
        evidence_id="evidence-1",
        source_id="source-1",
        summary="Current vendor capability documentation",
        captured_at=NOW,
        valid_until=None if valid_for_days is None else NOW + timedelta(days=valid_for_days),
        data_class=DataClass.PUBLIC,
        retention_days=None,
        payload_sha256=sha256_text("payload"),
    )


def fact(*, materiality: Materiality = Materiality.MEDIUM) -> KnowledgeClaim:
    return KnowledgeClaim(
        claim_id="fact-1",
        kind=ClaimKind.FACT,
        subject="provider-x",
        predicate="supports",
        value="canary",
        materiality=materiality,
        evidence_ids=("evidence-1",),
    )


class KnowledgeTests(unittest.TestCase):
    def test_fact_requires_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            KnowledgeClaim(
                claim_id="fact",
                kind=ClaimKind.FACT,
                subject="x",
                predicate="is",
                value="y",
                materiality=Materiality.HIGH,
            ).validate()

    def test_assumption_can_exist_without_evidence(self) -> None:
        KnowledgeClaim(
            claim_id="assumption",
            kind=ClaimKind.ASSUMPTION,
            subject="x",
            predicate="might",
            value="y",
            materiality=Materiality.MEDIUM,
        ).validate()

    def test_unresolved_material_contradiction_blocks_critical_decision(self) -> None:
        a = fact()
        b = KnowledgeClaim(
            claim_id="fact-2",
            kind=ClaimKind.FACT,
            subject="provider-x",
            predicate="supports",
            value="no-canary",
            materiality=Materiality.MEDIUM,
            evidence_ids=("evidence-1",),
        )
        contradiction = KnowledgeClaim(
            claim_id="contradiction-1",
            kind=ClaimKind.CONTRADICTION,
            subject="provider-x",
            predicate="supports",
            value="conflicting canary support",
            materiality=Materiality.HIGH,
            contradicts_claim_ids=("fact-1", "fact-2"),
        )
        snapshot = KnowledgeSnapshot((source(),), (evidence(),), (a, b, contradiction))
        self.assertEqual(
            snapshot.critical_decision_blockers(at=NOW),
            ("unresolved-contradiction:contradiction-1",),
        )

    def test_resolved_contradiction_does_not_block(self) -> None:
        a = fact()
        b = KnowledgeClaim(
            claim_id="fact-2",
            kind=ClaimKind.FACT,
            subject="provider-x",
            predicate="supports",
            value="no-canary",
            materiality=Materiality.MEDIUM,
            evidence_ids=("evidence-1",),
        )
        contradiction = KnowledgeClaim(
            claim_id="contradiction-1",
            kind=ClaimKind.CONTRADICTION,
            subject="provider-x",
            predicate="supports",
            value="resolved",
            materiality=Materiality.HIGH,
            contradicts_claim_ids=("fact-1", "fact-2"),
            resolved=True,
        )
        snapshot = KnowledgeSnapshot((source(),), (evidence(),), (a, b, contradiction))
        self.assertEqual(snapshot.critical_decision_blockers(at=NOW), ())

    def test_stale_critical_evidence_blocks(self) -> None:
        snapshot = KnowledgeSnapshot(
            (source(valid_for_days=None),),
            (evidence(valid_for_days=1),),
            (fact(materiality=Materiality.CRITICAL),),
        )
        blockers = snapshot.critical_decision_blockers(at=NOW + timedelta(days=2))
        self.assertEqual(blockers, ("stale-critical-evidence:fact-1:evidence-1",))

    def test_stale_critical_source_blocks(self) -> None:
        snapshot = KnowledgeSnapshot(
            (source(valid_for_days=1),),
            (evidence(valid_for_days=None),),
            (fact(materiality=Materiality.CRITICAL),),
        )
        blockers = snapshot.critical_decision_blockers(at=NOW + timedelta(days=2))
        self.assertEqual(blockers, ("stale-critical-source:fact-1:source-1",))

    def test_non_expiring_source_and_evidence_remain_fresh(self) -> None:
        snapshot = KnowledgeSnapshot(
            (source(valid_for_days=None),),
            (evidence(valid_for_days=None),),
            (fact(materiality=Materiality.CRITICAL),),
        )
        self.assertEqual(
            snapshot.critical_decision_blockers(at=NOW + timedelta(days=3650)),
            (),
        )

    def test_unknown_evidence_reference_is_rejected(self) -> None:
        broken = KnowledgeClaim(
            claim_id="fact-broken",
            kind=ClaimKind.FACT,
            subject="x",
            predicate="is",
            value="y",
            materiality=Materiality.HIGH,
            evidence_ids=("missing",),
        )
        with self.assertRaisesRegex(ValueError, "unknown evidence"):
            KnowledgeSnapshot((source(),), (evidence(),), (broken,)).validate()

    def test_restricted_evidence_requires_retention(self) -> None:
        row = EvidenceRef(
            evidence_id="restricted",
            source_id="source-1",
            summary="Internal evidence",
            captured_at=NOW,
            valid_until=None,
            data_class=DataClass.RESTRICTED,
            retention_days=None,
            payload_sha256=sha256_text("payload"),
        )
        with self.assertRaisesRegex(ValueError, "retention"):
            row.validate()

    def test_evidence_summary_rejects_raw_secret_marker(self) -> None:
        row = EvidenceRef(
            evidence_id="secret",
            source_id="source-1",
            summary="api_key=abcd",
            captured_at=NOW,
            valid_until=None,
            data_class=DataClass.RESTRICTED,
            retention_days=1,
            payload_sha256=sha256_text("payload"),
        )
        with self.assertRaisesRegex(ValueError, "secret"):
            row.validate()

    def test_provider_edition_capability_graph_validates(self) -> None:
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
                "rel-capability",
                "provider-x-pro",
                RelationshipKind.PROVIDES,
                "canary",
                ("evidence-1",),
            ),
        )
        KnowledgeSnapshot((source(),), (evidence(),), (), nodes, relationships).validate()

    def test_unknown_capability_node_reference_is_rejected(self) -> None:
        relation = CapabilityRelationship(
            "rel-1",
            "missing",
            RelationshipKind.PROVIDES,
            "canary",
        )
        nodes = (CapabilityNode("canary", NodeType.CAPABILITY, "Canary"),)
        with self.assertRaisesRegex(ValueError, "unknown capability node"):
            KnowledgeSnapshot((), (), (), nodes, (relation,)).validate()


if __name__ == "__main__":
    unittest.main()
