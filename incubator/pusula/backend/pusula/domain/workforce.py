from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .goal_scope import GoalRevision, ScopeCategory


class WorkforceRole(StrEnum):
    PRODUCT_MANAGER = "product-manager"
    LEAD_ENGINEER = "lead-engineer"
    FRONTEND_ENGINEER = "frontend-engineer"
    BACKEND_ENGINEER = "backend-engineer"
    UX_DESIGNER = "ux-designer"
    QA_ENGINEER = "qa-engineer"
    SECURITY_REVIEWER = "security-reviewer"
    RELEASE_ENGINEER = "release-engineer"
    RESEARCHER = "researcher"
    INDEPENDENT_REVIEWER = "independent-reviewer"


@dataclass(frozen=True, slots=True)
class WorkforceAssignment:
    role: WorkforceRole
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkforcePlan:
    goal_id: str
    revision: int
    assignments: tuple[WorkforceAssignment, ...]


_ROLE_RULES: tuple[tuple[WorkforceRole, tuple[str, ...]], ...] = (
    (
        WorkforceRole.FRONTEND_ENGINEER,
        ("frontend", "react", "web", "browser", "ui", "landing", "dashboard"),
    ),
    (
        WorkforceRole.BACKEND_ENGINEER,
        ("backend", "api", "django", "database", "postgres", "auth", "server"),
    ),
    (
        WorkforceRole.UX_DESIGNER,
        ("ux", "ui", "design", "accessibility", "responsive", "wcag", "landing"),
    ),
    (
        WorkforceRole.SECURITY_REVIEWER,
        ("security", "auth", "secret", "credential", "payment", "tenant", "permission"),
    ),
    (
        WorkforceRole.RELEASE_ENGINEER,
        ("deploy", "deployment", "production", "release", "docker", "ci", "rollback"),
    ),
    (
        WorkforceRole.RESEARCHER,
        ("research", "compare", "benchmark", "latest", "vendor", "pricing", "license"),
    ),
)


def _add_reason(
    roles: dict[WorkforceRole, set[str]],
    role: WorkforceRole,
    reason: str,
) -> None:
    roles.setdefault(role, set()).add(reason)


def plan_workforce(revision: GoalRevision) -> WorkforcePlan:
    revision.validate()
    text = revision.statement.casefold()
    risk_units = sum(unit.category is ScopeCategory.RISK for unit in revision.scope_units)
    change_units = sum(unit.category is ScopeCategory.CHANGE for unit in revision.scope_units)

    roles: dict[WorkforceRole, set[str]] = {
        WorkforceRole.PRODUCT_MANAGER: {"goal-owned"},
        WorkforceRole.QA_ENGINEER: {"verification-required"},
    }
    for role, terms in _ROLE_RULES:
        for term in terms:
            if term in text:
                _add_reason(roles, role, f"signal:{term}")

    if (
        WorkforceRole.FRONTEND_ENGINEER in roles
        or WorkforceRole.BACKEND_ENGINEER in roles
        or change_units
    ):
        _add_reason(roles, WorkforceRole.LEAD_ENGINEER, "implementation-coordination")
    if risk_units:
        _add_reason(roles, WorkforceRole.INDEPENDENT_REVIEWER, "risk-present")

    assignments = tuple(
        WorkforceAssignment(role=role, reason_codes=tuple(sorted(reasons)))
        for role, reasons in sorted(roles.items(), key=lambda row: row[0].value)
    )
    return WorkforcePlan(
        goal_id=revision.goal_id,
        revision=revision.revision,
        assignments=assignments,
    )
