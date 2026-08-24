from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from pusula.domain.goal_scope import (
    GoalRevision,
    ScopeCategory,
    ScopeUnit,
    build_revision,
    build_scope_slices,
)
from pusula.domain.workforce import WorkforceRole, plan_workforce


def units(
    count: int,
    *,
    category: ScopeCategory = ScopeCategory.ACCEPTANCE,
) -> tuple[ScopeUnit, ...]:
    return tuple(
        ScopeUnit(f"{category.value}-{index:03d}", category, f"unit {index}")
        for index in range(1, count + 1)
    )


class GoalScopeTests(unittest.TestCase):
    def test_automatic_execution_requires_four_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least four"):
            build_revision(goal_id="goal-1", statement="ship", scope_units=units(3))

    def test_scope_property_never_exceeds_quarter(self) -> None:
        for count in range(4, 65):
            slices = build_scope_slices(units(count))
            self.assertGreaterEqual(len(slices), 4)
            self.assertEqual(sum(len(row.units) for row in slices), count)
            for row in slices:
                self.assertLessEqual(len(row.units) * 4, count)

    def test_scope_unit_ids_must_be_unique(self) -> None:
        duplicate = ScopeUnit("same", ScopeCategory.ACCEPTANCE, "duplicate")
        with self.assertRaisesRegex(ValueError, "unique"):
            build_scope_slices((duplicate, duplicate, *units(2)))

    def test_scope_plan_is_deterministic(self) -> None:
        source = (
            ScopeUnit("b", ScopeCategory.RISK, "risk"),
            ScopeUnit("a", ScopeCategory.CHANGE, "change"),
            ScopeUnit("d", ScopeCategory.ACCEPTANCE, "acceptance"),
            ScopeUnit("c", ScopeCategory.ACCEPTANCE, "acceptance"),
        )
        self.assertEqual(build_scope_slices(source), build_scope_slices(reversed(source)))

    def test_revision_chain_is_monotonic(self) -> None:
        first = build_revision(goal_id="goal-1", statement="first", scope_units=units(4))
        second = build_revision(
            goal_id="goal-1",
            statement="second",
            scope_units=units(5),
            previous=first,
        )
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.supersedes_revision, 1)
        self.assertEqual(first.statement, "first")

    def test_revision_is_immutable(self) -> None:
        revision = build_revision(goal_id="goal-1", statement="first", scope_units=units(4))
        with self.assertRaises(FrozenInstanceError):
            revision.statement = "mutated"  # type: ignore[misc]

    def test_previous_revision_must_belong_to_same_goal(self) -> None:
        first = build_revision(goal_id="goal-1", statement="first", scope_units=units(4))
        with self.assertRaisesRegex(ValueError, "different goal"):
            build_revision(
                goal_id="goal-2",
                statement="second",
                scope_units=units(4),
                previous=first,
            )


class WorkforceTests(unittest.TestCase):
    def revision(
        self,
        statement: str,
        *,
        risk: int = 0,
        change: int = 4,
    ) -> GoalRevision:
        scope = list(units(change, category=ScopeCategory.CHANGE))
        scope.extend(units(risk, category=ScopeCategory.RISK))
        while len(scope) < 4:
            scope.extend(units(1, category=ScopeCategory.ACCEPTANCE))
        return build_revision(goal_id="goal-1", statement=statement, scope_units=scope)

    def roles(
        self,
        statement: str,
        *,
        risk: int = 0,
        change: int = 4,
    ) -> set[WorkforceRole]:
        plan = plan_workforce(self.revision(statement, risk=risk, change=change))
        return {row.role for row in plan.assignments}

    def test_landing_page_gets_frontend_and_ux_team(self) -> None:
        roles = self.roles("React landing page responsive UI")
        self.assertIn(WorkforceRole.PRODUCT_MANAGER, roles)
        self.assertIn(WorkforceRole.FRONTEND_ENGINEER, roles)
        self.assertIn(WorkforceRole.UX_DESIGNER, roles)
        self.assertIn(WorkforceRole.QA_ENGINEER, roles)
        self.assertIn(WorkforceRole.LEAD_ENGINEER, roles)

    def test_backend_auth_production_adds_specialists(self) -> None:
        roles = self.roles("Django API auth production deploy", risk=2)
        self.assertIn(WorkforceRole.BACKEND_ENGINEER, roles)
        self.assertIn(WorkforceRole.SECURITY_REVIEWER, roles)
        self.assertIn(WorkforceRole.RELEASE_ENGINEER, roles)
        self.assertIn(WorkforceRole.INDEPENDENT_REVIEWER, roles)

    def test_risk_requires_independent_reviewer(self) -> None:
        self.assertIn(
            WorkforceRole.INDEPENDENT_REVIEWER,
            self.roles("small change", risk=1),
        )

    def test_no_risk_avoids_unnecessary_independent_reviewer(self) -> None:
        self.assertNotIn(
            WorkforceRole.INDEPENDENT_REVIEWER,
            self.roles("small change", risk=0),
        )

    def test_workforce_plan_contains_roles_not_provider_names(self) -> None:
        plan = plan_workforce(self.revision("React API"))
        rendered = repr(plan).casefold()
        for provider_name in ("codex", "claude", "gemini", "openai", "anthropic"):
            self.assertNotIn(provider_name, rendered)

    def test_workforce_plan_is_deterministic(self) -> None:
        revision = self.revision("React API auth production", risk=1)
        self.assertEqual(plan_workforce(revision), plan_workforce(revision))
