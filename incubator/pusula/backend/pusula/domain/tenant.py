from __future__ import annotations

from dataclasses import dataclass

from pusula.domain.authorization import Action, Role, allows


class TenantAccessError(PermissionError):
    pass


@dataclass(frozen=True)
class MembershipSnapshot:
    team_id: str
    identity_subject: str
    role: Role


def authorize_membership(
    membership: MembershipSnapshot | None,
    *,
    identity_subject: str,
    requested_team_id: str,
    action: Action,
) -> MembershipSnapshot:
    if membership is None:
        raise TenantAccessError("membership required")
    if membership.identity_subject != identity_subject:
        raise TenantAccessError("identity mismatch")
    if membership.team_id != requested_team_id:
        raise TenantAccessError("team mismatch")
    if not allows(membership.role, action):
        raise TenantAccessError("action not permitted")
    return membership
