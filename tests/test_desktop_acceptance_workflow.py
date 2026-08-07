from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-acceptance.yml"


class DesktopAcceptanceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_acceptance_is_manual_main_only_and_protected(self) -> None:
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn("runs-on: [self-hosted, Windows, X64, divan-release-acceptance]", self.text)
        self.assertIn("environment: desktop-acceptance", self.text)

    def test_acceptance_runner_must_have_both_real_agents(self) -> None:
        self.assertIn('foreach ($agent in @("codex", "claude"))', self.text)
        self.assertIn("scripts/windows_desktop_acceptance.ps1", self.text)
        self.assertIn("--source-commit $sourceCommit", self.text)
        self.assertIn("--source-tree $sourceTree", self.text)

    def test_evidence_is_attested_and_uploaded(self) -> None:
        self.assertIn("id-token: write", self.text)
        self.assertIn("attestations: write", self.text)
        self.assertIn("actions/attest-build-provenance@", self.text)
        self.assertIn("name: divan-windows-acceptance", self.text)
        self.assertIn("retention-days: 30", self.text)

    def test_no_release_or_api_secrets_are_exposed_to_acceptance_job(self) -> None:
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY", self.text)
        self.assertNotIn("OPENAI_API_KEY", self.text)
        self.assertNotIn("ANTHROPIC_API_KEY", self.text)

    def test_all_actions_are_immutable_sha_pinned(self) -> None:
        mutable = []
        for number, line in enumerate(self.text.splitlines(), 1):
            if "uses:" not in line or line.lstrip().startswith("#"):
                continue
            if not re.search(r"uses:\s+[^\s@]+@[0-9a-f]{40}\s+#\s+v\d+", line):
                mutable.append(f"{number}: {line.strip()}")
        self.assertEqual(mutable, [])


if __name__ == "__main__":
    unittest.main()
