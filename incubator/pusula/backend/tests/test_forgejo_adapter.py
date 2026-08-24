from __future__ import annotations

import json
from typing import Any
from unittest import TestCase

from pusula.integrations.forgejo import ForgejoClient, ForgejoConfig


class _Response:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload


class _Opener:
    def __init__(self, *payloads: object) -> None:
        self.payloads = list(payloads)
        self.requests: list[Any] = []
        self.timeouts: list[float] = []

    def __call__(self, request: Any, *, timeout: float) -> _Response:
        self.requests.append(request)
        self.timeouts.append(timeout)
        return _Response(self.payloads.pop(0))


class ForgejoAdapterTests(TestCase):
    def config(self) -> ForgejoConfig:
        return ForgejoConfig(base_url="https://forgejo.example", token="super-secret", timeout_seconds=7)

    def test_token_is_hidden_from_config_repr(self) -> None:
        self.assertNotIn("super-secret", repr(self.config()))

    def test_version_uses_token_auth_and_api_prefix(self) -> None:
        opener = _Opener({"version": "15.0.7"})
        client = ForgejoClient(self.config(), opener=opener)

        self.assertEqual(client.version(), "15.0.7")
        request = opener.requests[0]
        self.assertEqual(request.full_url, "https://forgejo.example/api/v1/version")
        self.assertEqual(request.get_header("Authorization"), "token super-secret")
        self.assertEqual(opener.timeouts, [7])

    def test_list_repositories_normalizes_provider_payload(self) -> None:
        opener = _Opener(
            [
                {
                    "owner": {"login": "pusula"},
                    "name": "demo",
                    "default_branch": "main",
                    "clone_url": "https://forgejo.example/pusula/demo.git",
                    "private": True,
                }
            ]
        )
        client = ForgejoClient(self.config(), opener=opener)

        repos = client.list_repositories()

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].full_name, "pusula/demo")
        self.assertTrue(repos[0].private)

    def test_create_branch_posts_explicit_source_and_target(self) -> None:
        opener = _Opener({})
        client = ForgejoClient(self.config(), opener=opener)

        client.create_branch("pusula", "demo", branch="feat/test", from_branch="main")

        request = opener.requests[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {"new_branch_name": "feat/test", "old_branch_name": "main"},
        )

    def test_create_pull_request_normalizes_response(self) -> None:
        opener = _Opener(
            {
                "number": 42,
                "title": "Test",
                "state": "open",
                "head": {"ref": "feat/test"},
                "base": {"ref": "main"},
                "html_url": "https://forgejo.example/pusula/demo/pulls/42",
            }
        )
        client = ForgejoClient(self.config(), opener=opener)

        pull = client.create_pull_request(
            "pusula",
            "demo",
            title="Test",
            head_branch="feat/test",
            base_branch="main",
            body="Evidence first",
        )

        self.assertEqual(pull.number, 42)
        self.assertEqual(pull.head_branch, "feat/test")
        self.assertEqual(pull.base_branch, "main")
