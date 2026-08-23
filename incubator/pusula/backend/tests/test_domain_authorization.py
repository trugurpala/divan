from __future__ import annotations

import unittest

from pusula.domain.authorization import Action, Role, allows


class AuthorizationTests(unittest.TestCase):
    def test_owner_allows_every_action(self) -> None:
        for action in Action:
            self.assertTrue(allows(Role.OWNER, action), action)

    def test_member_cannot_manage_members(self) -> None:
        self.assertFalse(allows(Role.MEMBER, Action.MANAGE_MEMBERS))

    def test_member_cannot_deploy(self) -> None:
        self.assertFalse(allows(Role.MEMBER, Action.DEPLOY))

    def test_member_can_create_goal(self) -> None:
        self.assertTrue(allows(Role.MEMBER, Action.CREATE_GOAL))

    def test_viewer_can_only_read(self) -> None:
        self.assertTrue(allows(Role.VIEWER, Action.READ))
        for action in Action:
            if action is not Action.READ:
                self.assertFalse(allows(Role.VIEWER, action), action)
