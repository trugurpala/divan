from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_agent_preflight.py"
SPEC = importlib.util.spec_from_file_location("desktop_agent_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DesktopAgentPreflightTests(unittest.TestCase):
    def test_codex_chatgpt_login_is_accepted(self) -> None:
        self.assertEqual(MODULE.parse_codex_auth("Logged in using ChatGPT"), "chatgpt")

    def test_codex_api_and_agent_identity_logins_are_accepted(self) -> None:
        self.assertEqual(
            MODULE.parse_codex_auth("Logged in using an API key"), "api-key"
        )
        self.assertEqual(
            MODULE.parse_codex_auth("Logged in using agent identity"),
            "agent-identity",
        )

    def test_codex_missing_or_unknown_auth_fails_closed(self) -> None:
        with self.assertRaises(MODULE.AgentPreflightError):
            MODULE.parse_codex_auth("Not logged in")
        with self.assertRaises(MODULE.AgentPreflightError):
            MODULE.parse_codex_auth("codex 1.0")

    def test_codex_probe_requires_exact_final_marker(self) -> None:
        good = "\n".join(
            (
                json.dumps({"type": "turn.started"}),
                json.dumps({"item": {"text": "DIVAN_AUTH_OK"}}),
            )
        )
        MODULE.parse_codex_probe(good)
        for value in (
            "not-json",
            json.dumps({"item": {"text": "almost DIVAN_AUTH_OK"}}),
            json.dumps({"message": "DIVAN_AUTH_OK extra"}),
            json.dumps({"type": "turn.completed"}),
        ):
            with self.subTest(value=value):
                with self.assertRaises(MODULE.AgentPreflightError):
                    MODULE.parse_codex_probe(value)

    def test_claude_probe_requires_exact_json_marker(self) -> None:
        MODULE.parse_claude_probe('{"result":"DIVAN_AUTH_OK"}')
        for value in (
            "not-json",
            "[]",
            '{"result":"almost DIVAN_AUTH_OK"}',
            '{"result":"DIVAN_AUTH_OK extra"}',
            '{}',
        ):
            with self.subTest(value=value):
                with self.assertRaises(MODULE.AgentPreflightError):
                    MODULE.parse_claude_probe(value)

    def test_preflight_invocations_are_read_only_non_shell_probes(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("shell=False", text)
        self.assertIn('(codex, "login", "status")', text)
        self.assertIn('"--sandbox",\n            "read-only"', text)
        self.assertIn('"--ephemeral"', text)
        self.assertIn('"--permission-mode",\n            "plan"', text)
        self.assertIn('"--max-turns",\n            "1"', text)
        self.assertIn("Do not use tools, edit files, or run commands", text)


if __name__ == "__main__":
    unittest.main()
