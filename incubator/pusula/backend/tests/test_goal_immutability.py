from __future__ import annotations

import uuid

from django.test import TestCase
from pusula.domain.goal_scope import ScopeCategory, ScopeUnit
from pusula.mizan.goal_services import create_goal


def scope_units() -> tuple[ScopeUnit, ...]:
    return tuple(
        ScopeUnit(
            unit_id=f"change-{index:03d}",
            category=ScopeCategory.CHANGE,
            description=f"change {index}",
        )
        for index in range(1, 5)
    )


class GoalImmutabilityTests(TestCase):
    def create(self):
        return create_goal(
            team_id=uuid.uuid4(),
            statement="immutable goal",
            scope_units=scope_units(),
            idempotency_key="immutable-goal",
            correlation_id=uuid.uuid4(),
        )

    def test_goal_instance_cannot_be_updated(self) -> None:
        result = self.create()
        result.goal.team_id = uuid.uuid4()
        with self.assertRaisesRegex(TypeError, "append-only"):
            result.goal.save()

    def test_goal_instance_cannot_be_deleted(self) -> None:
        result = self.create()
        with self.assertRaisesRegex(TypeError, "append-only"):
            result.goal.delete()
