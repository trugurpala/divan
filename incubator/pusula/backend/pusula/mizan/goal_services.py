from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Iterable

from django.db import transaction

from pusula.domain.goal_scope import (
    GoalRevision as DomainGoalRevision,
    ScopeCategory,
    ScopeSlice,
    ScopeUnit,
    build_revision,
    build_scope_slices,
)
from pusula.domain.workforce import WorkforcePlan, plan_workforce

from .models import Goal, GoalRevision, ScopeSliceRecord
from .services import MutationResult, record_mutation


@dataclass(frozen=True, slots=True)
class GoalMutationResult:
    goal: Goal
    revision: GoalRevision
    workforce: WorkforcePlan
    mutation: MutationResult


def _serialize_units(units: tuple[ScopeUnit, ...]) -> list[dict[str, str]]:
    return [
        {
            "id": unit.unit_id,
            "category": unit.category.value,
            "description": unit.description,
        }
        for unit in units
    ]


def _domain_revision(model: GoalRevision) -> DomainGoalRevision:
    units = tuple(
        ScopeUnit(
            unit_id=str(row["id"]),
            category=ScopeCategory(str(row["category"])),
            description=str(row["description"]),
        )
        for row in model.scope_units
    )
    supersedes = model.supersedes.revision if model.supersedes_id is not None else None
    return DomainGoalRevision(
        goal_id=str(model.goal_id),
        revision=model.revision,
        statement=model.statement,
        scope_units=units,
        supersedes_revision=supersedes,
    )


def _persist_slices(
    *,
    team_id: uuid.UUID,
    revision: GoalRevision,
    slices: tuple[ScopeSlice, ...],
) -> None:
    ScopeSliceRecord.objects.bulk_create(
        [
            ScopeSliceRecord(
                team_id=team_id,
                revision=revision,
                slice_id=row.slice_id,
                unit_ids=[unit.unit_id for unit in row.units],
            )
            for row in slices
        ]
    )


def _event_payload(
    revision: DomainGoalRevision,
    slices: tuple[ScopeSlice, ...],
    workforce: WorkforcePlan,
) -> dict[str, Any]:
    return {
        "goal_id": revision.goal_id,
        "revision": revision.revision,
        "scope_unit_count": len(revision.scope_units),
        "scope_slice_count": len(slices),
        "workforce_roles": [row.role.value for row in workforce.assignments],
    }


def _load_result(
    *,
    team_id: uuid.UUID,
    mutation: MutationResult,
) -> GoalMutationResult:
    payload = mutation.event.payload
    goal_id = uuid.UUID(str(payload["goal_id"]))
    revision_number = int(payload["revision"])
    goal = Goal.objects.get(id=goal_id, team_id=team_id)
    revision = GoalRevision.objects.get(
        goal=goal,
        team_id=team_id,
        revision=revision_number,
    )
    return GoalMutationResult(
        goal=goal,
        revision=revision,
        workforce=plan_workforce(_domain_revision(revision)),
        mutation=mutation,
    )


def create_goal(
    *,
    team_id: uuid.UUID,
    statement: str,
    scope_units: Iterable[ScopeUnit],
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> GoalMutationResult:
    goal_id = uuid.uuid4()
    revision = build_revision(
        goal_id=str(goal_id),
        statement=statement,
        scope_units=scope_units,
    )
    slices = build_scope_slices(revision.scope_units)
    workforce = plan_workforce(revision)
    payload = _event_payload(revision, slices, workforce)

    def mutate_projection() -> None:
        goal = Goal.objects.create(id=goal_id, team_id=team_id)
        stored_revision = GoalRevision.objects.create(
            team_id=team_id,
            goal=goal,
            revision=revision.revision,
            statement=revision.statement,
            scope_units=_serialize_units(revision.scope_units),
        )
        _persist_slices(team_id=team_id, revision=stored_revision, slices=slices)

    mutation = record_mutation(
        team_id=team_id,
        aggregate_type="goal",
        aggregate_id=goal_id,
        event_type="goal.created",
        event_payload=payload,
        topic="mizan.goal.created",
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        mutate_projection=mutate_projection,
    )
    return _load_result(team_id=team_id, mutation=mutation)


@transaction.atomic
def append_goal_revision(
    *,
    team_id: uuid.UUID,
    goal_id: uuid.UUID,
    statement: str,
    scope_units: Iterable[ScopeUnit],
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> GoalMutationResult:
    goal = Goal.objects.select_for_update().get(id=goal_id, team_id=team_id)
    previous_model = goal.revisions.order_by("-revision").first()
    if previous_model is None:
        raise RuntimeError("goal has no initial revision")
    previous = _domain_revision(previous_model)
    revision = build_revision(
        goal_id=str(goal.id),
        statement=statement,
        scope_units=scope_units,
        previous=previous,
    )
    slices = build_scope_slices(revision.scope_units)
    workforce = plan_workforce(revision)
    payload = _event_payload(revision, slices, workforce)

    def mutate_projection() -> None:
        stored_revision = GoalRevision.objects.create(
            team_id=team_id,
            goal=goal,
            revision=revision.revision,
            statement=revision.statement,
            scope_units=_serialize_units(revision.scope_units),
            supersedes=previous_model,
        )
        _persist_slices(team_id=team_id, revision=stored_revision, slices=slices)

    mutation = record_mutation(
        team_id=team_id,
        aggregate_type="goal",
        aggregate_id=goal.id,
        event_type="goal.revised",
        event_payload=payload,
        topic="mizan.goal.revised",
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        mutate_projection=mutate_projection,
    )
    return _load_result(team_id=team_id, mutation=mutation)
