from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable

from django.db import IntegrityError, transaction

from .models import DomainEvent, OutboxMessage


@dataclass(frozen=True)
class MutationResult:
    event: DomainEvent
    created: bool


@transaction.atomic
def record_mutation(
    *,
    team_id: uuid.UUID,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    event_type: str,
    event_payload: dict[str, Any],
    topic: str,
    idempotency_key: str,
    correlation_id: uuid.UUID,
    mutate_projection: Callable[[], None],
) -> MutationResult:
    existing = DomainEvent.objects.filter(team_id=team_id, idempotency_key=idempotency_key).first()
    if existing is not None:
        return MutationResult(event=existing, created=False)

    mutate_projection()
    try:
        event = DomainEvent.objects.create(
            team_id=team_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=event_payload,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
    except IntegrityError:
        event = DomainEvent.objects.get(team_id=team_id, idempotency_key=idempotency_key)
        return MutationResult(event=event, created=False)

    OutboxMessage.objects.create(
        team_id=team_id,
        event=event,
        topic=topic,
        payload=event_payload,
    )
    return MutationResult(event=event, created=True)
