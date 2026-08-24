from __future__ import annotations

import uuid

from django.db import models


class AppendOnlyModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args: object, **kwargs: object) -> None:
        if not self._state.adding:
            raise TypeError(f"{type(self).__name__} is append-only")
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> None:
        raise TypeError(f"{type(self).__name__} is append-only")


class DomainEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    aggregate_type = models.CharField(max_length=80)
    aggregate_id = models.UUIDField()
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    correlation_id = models.UUIDField()
    idempotency_key = models.CharField(max_length=255)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "idempotency_key"],
                name="pusula_unique_team_idempotency",
            ),
        ]
        indexes = [
            models.Index(fields=["team_id", "aggregate_type", "aggregate_id"]),
            models.Index(fields=["correlation_id"]),
        ]


class OutboxMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    event = models.OneToOneField(
        DomainEvent,
        on_delete=models.PROTECT,
        related_name="outbox",
    )
    topic = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)


class Goal(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)


class GoalRevision(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    goal = models.ForeignKey(Goal, on_delete=models.PROTECT, related_name="revisions")
    revision = models.PositiveIntegerField()
    statement = models.TextField()
    scope_units = models.JSONField(default=list)
    supersedes = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        related_name="superseded_by",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["goal", "revision"],
                name="pusula_unique_goal_revision",
            ),
        ]


class ScopeSliceRecord(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    revision = models.ForeignKey(
        GoalRevision,
        on_delete=models.PROTECT,
        related_name="scope_slices",
    )
    slice_id = models.CharField(max_length=80)
    unit_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "slice_id"],
                name="pusula_unique_revision_slice",
            ),
        ]


class KnowledgeSource(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    source_key = models.CharField(max_length=255)
    locator = models.TextField()
    authority = models.CharField(max_length=120)
    observed_at = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    content_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "source_key"],
                name="pusula_unique_team_source_key",
            ),
        ]


class EvidenceArtifact(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    evidence_key = models.CharField(max_length=255)
    source = models.ForeignKey(
        KnowledgeSource,
        on_delete=models.PROTECT,
        related_name="evidence_artifacts",
    )
    summary = models.TextField()
    captured_at = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    data_class = models.CharField(max_length=24)
    retention_days = models.PositiveIntegerField(null=True, blank=True)
    payload_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "evidence_key"],
                name="pusula_unique_team_evidence_key",
            ),
        ]


class KnowledgeClaimRecord(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    claim_key = models.CharField(max_length=255)
    kind = models.CharField(max_length=24)
    subject = models.CharField(max_length=255)
    predicate = models.CharField(max_length=255)
    value = models.TextField()
    materiality = models.CharField(max_length=24)
    evidence_keys = models.JSONField(default=list)
    contradicts_claim_keys = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "claim_key"],
                name="pusula_unique_team_claim_key",
            ),
        ]


class ContradictionResolutionRecord(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    resolution_key = models.CharField(max_length=255)
    contradiction_claim_key = models.CharField(max_length=255)
    summary = models.TextField()
    evidence_keys = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "resolution_key"],
                name="pusula_unique_team_resolution_key",
            ),
        ]


class CapabilityGraphNode(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    node_key = models.CharField(max_length=255)
    node_type = models.CharField(max_length=24)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "node_key"],
                name="pusula_unique_team_capability_node",
            ),
        ]


class CapabilityGraphRelationship(AppendOnlyModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    relationship_key = models.CharField(max_length=255)
    source_node = models.ForeignKey(
        CapabilityGraphNode,
        on_delete=models.PROTECT,
        related_name="outgoing_relationships",
    )
    kind = models.CharField(max_length=24)
    target_node = models.ForeignKey(
        CapabilityGraphNode,
        on_delete=models.PROTECT,
        related_name="incoming_relationships",
    )
    evidence_keys = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team_id", "relationship_key"],
                name="pusula_unique_team_capability_rel",
            ),
        ]
