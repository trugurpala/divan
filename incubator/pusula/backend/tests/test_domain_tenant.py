from __future__ import annotations

import unittest

from pusula.domain.authorization import Action, Role
from pusula.domain.tenant import MembershipSnapshot, TenantAccessError, authorize_membership


class TenantAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.owner = MembershipSnapshot("team-a", "user-1", Role.OWNER)
        self.member = MembershipSnapshot("team-a", "user-2", Role.MEMBER)
        self.viewer = MembershipSnapshot("team-a", "user-3", Role.VIEWER)

    def test_owner_can_manage_members(self) -> None:
        result = authorize_membership(
            self.owner,
            identity_subject="user-1",
            requested_team_id="team-a",
            action=Action.MANAGE_MEMBERS,
        )
        self.assertEqual(result.role, Role.OWNER)

    def test_rejects_missing_membership(self) -> None:
        with self.assertRaisesRegex(TenantAccessError, "membership required"):
            authorize_membership(
                None,
                identity_subject="user-1",
                requested_team_id="team-a",
                action=Action.READ,
            )

    def test_rejects_cross_team_access(self) -> None:
        with self.assertRaisesRegex(TenantAccessError, "team mismatch"):
            authorize_membership(
                self.owner,
                identity_subject="user-1",
                requested_team_id="team-b",
                action=Action.READ,
            )

    def test_rejects_identity_confusion(self) -> None:
        with self.assertRaisesRegex(TenantAccessError, "identity mismatch"):
            authorize_membership(
                self.owner,
                identity_subject="user-9",
                requested_team_id="team-a",
                action=Action.READ,
            )

    def test_member_cannot_deploy(self) -> None:
        with self.assertRaisesRegex(TenantAccessError, "action not permitted"):
            authorize_membership(
                self.member,
                identity_subject="user-2",
                requested_team_id="team-a",
                action=Action.DEPLOY,
            )

    def test_viewer_cannot_create_goal(self) -> None:
        with self.assertRaisesRegex(TenantAccessError, "action not permitted"):
            authorize_membership(
                self.viewer,
                identity_subject="user-3",
                requested_team_id="team-a",
                action=Action.CREATE_GOAL,
            )

    def test_viewer_can_read_own_team(self) -> None:
        result = authorize_membership(
            self.viewer,
            identity_subject="user-3",
            requested_team_id="team-a",
            action=Action.READ,
        )
        self.assertEqual(result.team_id, "team-a")


if __name__ == "__main__":
    unittest.main()
