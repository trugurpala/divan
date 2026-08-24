from __future__ import annotations

import uuid

from django.test import TestCase
from pusula.domain.goal_scope import ScopeCategory, ScopeUnit
from pusula.domain.workforce import WorkforceRole
from pusula.mizan.goal_services import append_goal_revision, create_goal
from pusula.mizan.models import (
    DomainEvent,
    Goal,
    GoalRevision,
    OutboxMessage,
    ScopeSliceRecord,
)


def scope_units(count: int = 4) -> tuple[ScopeUnit, ...]:
    return tuple(
        ScopeUnit(
            unit_id=f"change-{index:03d}",
            category=ScopeCategory.CHANGE,
            description=f"change {index}",
        )
        for index in range(1, count + 1)
    )


class GoalPersistenceTests(TestCase):
    def setUp(self) -> None:
        self.team_id = uuid.uuid4()

    def create(self, *, key: str = "goal-create-1"):
        return create_goal(
            team_id=self.team_id,
            statement="React API dashboard",
            scope_units=scope_units(),
            idempotency_key=key,
            correlation_id=uuid.uuid4(),
        )

    def test_create_goal_persists_revision_slices_event_and_outbox(self) -> None:
        result = self.create()
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(GoalRevision.objects.count(), 1)
        self.assertEqual(ScopeSliceRecord.objects.count(), 4)
        self.assertEqual(DomainEvent.objects.count(), 1)
        self.assertEqual(OutboxMessage.objects.count(), 1)
        self.assertEqual(result.revision.revision, 1)
        roles = {row.role for row in result.workforce.assignments}
        self.assertIn(WorkforceRole.FRONTEND_ENGINEER, roles)
        self.assertIn(WorkforceRole.BACKEND_ENGINEER, roles)

    def test_duplicate_idempotency_returns_same_goal_without_duplicate_projection(self) -> None:
        first = self.create(key="same-key")
        second = self.create(key="same-key")
        self.assertEqual(first.goal.id, second.goal.id)
        self.assertFalse(second.mutation.created)
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(GoalRevision.objects.count(), 1)
        self.assertEqual(DomainEvent.objects.count(), 1)
        self.assertEqual(OutboxMessage.objects.count(), 1)

    def test_append_revision_preserves_previous_revision(self) -> None:
        first = self.create()
        second = append_goal_revision(
            team_id=self.team_id,
            goal_id=first.goal.id,
            statement="React API dashboard with auth production deploy",
            scope_units=scope_units(5),
            idempotency_key="goal-revision-2",
            correlation_id=uuid.uuid4(),
        )
        self.assertEqual(second.revision.revision, 2)
        self.assertEqual(second.revision.supersedes_id, first.revision.id)
        first.revision.refresh_from_db()
        self.assertEqual(first.revision.statement, "React API dashboard")
        self.assertEqual(GoalRevision.objects.count(), 2)
        self.assertEqual(DomainEvent.objects.count(), 2)
        self.assertEqual(OutboxMessage.objects.count(), 2)

    def test_goal_revision_instance_cannot_be_updated(self) -> None:
        result = self.create()
        result.revision.statement = "mutated"
        with self.assertRaisesRegex(TypeError, "append-only"):
            result.revision.save()

    def test_goal_revision_instance_cannot_be_deleted(self) -> None:
        result = self.create()
        with self.assertRaisesRegex(TypeError, "append-only"):
            result.revision.delete()

    def test_revision_scope_slices_never_exceed_quarter(self) -> None:
        result = self.create()
        total_units = len(result.revision.scope_units)
        for row in result.revision.scope_slices.all():
            self.assertLessEqual(len(row.unit_ids) * 4, total_units)
