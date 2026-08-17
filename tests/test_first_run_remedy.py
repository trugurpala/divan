"""Who closes a capability that is not ready.

The wizard promised Divan would prepare a missing dependency and the Core never
sent anything for it to read, so the promise fell through to a fixed sentence.
These tests pin the line: a missing tool is Divan's job, a missing credential is
the owner's and only the owner's, and something already installed never gets an
install command however its reason code reads.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "plugins" / "sadrazam"))

from divan_runtime.doctor_checks import (  # noqa: E402
    build_report,
    report_payload,
    trusted_state_root,
)
from divan_runtime.first_run_remedy import (  # noqa: E402
    OWNER_ONLY_CODES,
    PREPARATION_COMMANDS,
    Remedy,
    RemedyKind,
    annotate_report,
    remedy_for,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


class WhoActsTests(unittest.TestCase):
    def test_a_certified_capability_needs_nothing(self):
        self.assertIs(
            remedy_for("codex", "CERTIFIED", None).kind, RemedyKind.NOTHING_TO_DO
        )

    def test_a_missing_tool_is_divan_s_job(self):
        remedy = remedy_for("codex", "OFFLINE", "TOOL_NOT_INSTALLED")

        self.assertIs(remedy.kind, RemedyKind.DIVAN_PREPARES)
        self.assertEqual(remedy.command, PREPARATION_COMMANDS["codex"])

    def test_a_missing_credential_is_the_owner_s_job(self):
        remedy = remedy_for("claude", "DEGRADED", "AUTH_REQUIRED", version="2.1.229")

        self.assertIs(remedy.kind, RemedyKind.OWNER_ACTION)
        self.assertIn("oturum", remedy.sentence)

    def test_an_owner_action_never_carries_a_command(self):
        # Divan must not be able to run a credential step on the owner's behalf,
        # so the shape itself refuses to hold one.
        with self.assertRaises(ValueError):
            Remedy(RemedyKind.OWNER_ACTION, "sign in", ("npm", "login"))

    def test_something_installed_is_never_told_to_install_again(self):
        remedy = remedy_for("codex", "DEGRADED", "SOMETHING_ELSE", version="0.147.0")

        self.assertIsNot(remedy.kind, RemedyKind.DIVAN_PREPARES)
        self.assertEqual(remedy.command, ())

    def test_a_tool_with_no_session_is_not_asked_to_sign_in(self):
        # Git reports an unverified session because the generic check cannot
        # verify one; git has none, so telling the owner to sign in is nonsense.
        remedy = remedy_for("git", "DEGRADED", "AUTH_NOT_VERIFIED", version="2.51.0")

        self.assertIsNot(remedy.kind, RemedyKind.OWNER_ACTION)

    def test_a_blocked_capability_says_so_plainly(self):
        remedy = remedy_for("local-state-security", "BLOCKED", "LOCAL_STATE_DACL_POLICY")

        self.assertIs(remedy.kind, RemedyKind.OUT_OF_REACH)
        self.assertIn("Windows", remedy.sentence)


class NoCredentialAutomationTests(unittest.TestCase):
    def test_no_preparation_command_touches_a_credential(self):
        for capability, command in PREPARATION_COMMANDS.items():
            flat = " ".join(command).casefold()
            for forbidden in ("login", "auth", "token", "password", "credential", "cookie"):
                with self.subTest(capability=capability, word=forbidden):
                    self.assertNotIn(forbidden, flat)

    def test_every_preparation_command_names_a_known_launcher(self):
        for capability, command in PREPARATION_COMMANDS.items():
            with self.subTest(capability=capability):
                self.assertIn(command[0], {"npm", "npx", "winget"})

    def test_the_auth_codes_the_doctor_actually_emits_are_owner_only(self):
        self.assertIn("AUTH_REQUIRED", OWNER_ONLY_CODES)
        self.assertIn("AUTH_NOT_VERIFIED", OWNER_ONLY_CODES)


class CanonicalPayloadTests(unittest.TestCase):
    def _payload(self):
        return report_payload(
            build_report(
                state_root=trusted_state_root(),
                knowledge_database=ROOT / ".divan" / "knowledge.db",
            )
        )

    def test_every_capability_carries_a_remedy_and_a_sentence(self):
        for capability in self._payload()["capabilities"]:
            with self.subTest(capability=capability["capability_id"]):
                self.assertIn("remedy", capability)
                self.assertTrue(capability["action_hint"].strip())

    def test_annotating_a_payload_without_capabilities_changes_nothing(self):
        self.assertEqual(annotate_report({"anything": 1}), {"anything": 1})

    def test_no_capability_is_offered_an_install_it_does_not_need(self):
        for capability in self._payload()["capabilities"]:
            if capability.get("version"):
                with self.subTest(capability=capability["capability_id"]):
                    self.assertEqual(capability["remedy"]["command"], [])


if __name__ == "__main__":
    unittest.main()
