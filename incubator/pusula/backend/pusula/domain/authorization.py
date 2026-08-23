from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Action(StrEnum):
    READ = "read"
    CREATE_GOAL = "create_goal"
    MUTATE_PROJECT = "mutate_project"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_PROVIDERS = "manage_providers"
    DEPLOY = "deploy"


_ALLOWED: dict[Role, frozenset[Action]] = {
    Role.OWNER: frozenset(Action),
    Role.MEMBER: frozenset({Action.READ, Action.CREATE_GOAL, Action.MUTATE_PROJECT}),
    Role.VIEWER: frozenset({Action.READ}),
}


def allows(role: Role, action: Action) -> bool:
    return action in _ALLOWED[role]
