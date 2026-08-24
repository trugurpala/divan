from __future__ import annotations

import uuid
from unittest.mock import patch

from django.test import Client, TestCase
from pusula.domain.identity import IdentityClaims
from pusula.mizan.models import DomainEvent, OutboxMessage
from pusula.mizan.services import record_mutation
from pusula.teams.models import Membership, Team


class _Verifier:
    def __init__(self, subject: str) -> None:
        self.subject = subject

    def verify(self, token: str, **_: object) -> IdentityClaims:
        if token != "valid-token":
            raise AssertionError("unexpected token")
        return IdentityClaims(
            subject=self.subject,
            issuer="https://id.example/oidc",
            audiences=frozenset({"https://api.example"}),
            scopes=frozenset({"projects:read"}),
            organization_id=None,
        )


class TenantApiTests(TestCase):
    def setUp(self) -> None:
        self.team_a = Team.objects.create(name="A")
        self.team_b = Team.objects.create(name="B")
        Membership.objects.create(team=self.team_a, identity_subject="user-1", role="member")
        self.client = Client(HTTP_AUTHORIZATION="Bearer valid-token")

    @patch("pusula.auth.request_context._logto_verifier", return_value=_Verifier("user-1"))
    def test_member_can_read_own_team(self, _: object) -> None:
        response = self.client.get(f"/api/teams/{self.team_a.id}/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["role"], "member")

    @patch("pusula.auth.request_context._logto_verifier", return_value=_Verifier("user-1"))
    def test_member_cannot_read_other_team(self, _: object) -> None:
        response = self.client.get(f"/api/teams/{self.team_b.id}/me")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "forbidden")

    def test_missing_token_is_unauthorized(self) -> None:
        response = Client().get(f"/api/teams/{self.team_a.id}/me")
        self.assertEqual(response.status_code, 401)


class MizanMutationTests(TestCase):
    def test_duplicate_key_mutates_projection_once(self) -> None:
        team_id = uuid.uuid4()
        aggregate_id = uuid.uuid4()
        correlation_id = uuid.uuid4()
        calls = 0

        def mutate() -> None:
            nonlocal calls
            calls += 1

        first = record_mutation(
            team_id=team_id,
            aggregate_type="goal",
            aggregate_id=aggregate_id,
            event_type="GoalCreated",
            event_payload={"title": "test"},
            topic="goal.created",
            idempotency_key="same",
            correlation_id=correlation_id,
            mutate_projection=mutate,
        )
        second = record_mutation(
            team_id=team_id,
            aggregate_type="goal",
            aggregate_id=aggregate_id,
            event_type="GoalCreated",
            event_payload={"title": "test"},
            topic="goal.created",
            idempotency_key="same",
            correlation_id=correlation_id,
            mutate_projection=mutate,
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(calls, 1)
        self.assertEqual(DomainEvent.objects.count(), 1)
        self.assertEqual(OutboxMessage.objects.count(), 1)

    def test_projection_failure_rolls_back_event_and_outbox(self) -> None:
        def explode() -> None:
            raise RuntimeError("projection failed")

        with self.assertRaisesRegex(RuntimeError, "projection failed"):
            record_mutation(
                team_id=uuid.uuid4(),
                aggregate_type="goal",
                aggregate_id=uuid.uuid4(),
                event_type="GoalCreated",
                event_payload={},
                topic="goal.created",
                idempotency_key="rollback",
                correlation_id=uuid.uuid4(),
                mutate_projection=explode,
            )

        self.assertEqual(DomainEvent.objects.count(), 0)
        self.assertEqual(OutboxMessage.objects.count(), 0)
