from __future__ import annotations

import uuid

from django.db import models


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
            models.UniqueConstraint(fields=["team_id", "idempotency_key"], name="pusula_unique_team_idempotency"),
        ]
        indexes = [
            models.Index(fields=["team_id", "aggregate_type", "aggregate_id"]),
            models.Index(fields=["correlation_id"]),
        ]


class OutboxMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_id = models.UUIDField()
    event = models.OneToOneField(DomainEvent, on_delete=models.PROTECT, related_name="outbox")
    topic = models.CharField(max_length=120)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
