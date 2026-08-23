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
