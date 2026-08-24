from __future__ import annotations

import uuid

from pusula.domain.authorization import Role
from pusula.domain.tenant import MembershipSnapshot
from pusula.teams.models import Membership


def get_membership_snapshot(*, team_id: uuid.UUID, identity_subject: str) -> MembershipSnapshot | None:
    membership = (
        Membership.objects.filter(team_id=team_id, identity_subject=identity_subject)
        .only("team_id", "identity_subject", "role")
        .first()
    )
    if membership is None:
        return None
    return MembershipSnapshot(
        team_id=str(membership.team_id),
        identity_subject=membership.identity_subject,
        role=Role(membership.role),
    )
