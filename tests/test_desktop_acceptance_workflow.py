from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-acceptance.yml"
ACCEPTANCE_SCRIPT = ROOT / "scripts" / "windows_desktop_acceptance.ps1"
PREFLIGHT_SCRIPT = ROOT / "scripts" / "desktop_agent_preflight.py"


class DesktopAcceptanceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_acceptance_is_manual_main_only_and_protected(self) -> None:
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn(
            "runs-on: [self-hosted, windows, x64, divan-desktop-acceptance]",
            self.text,
        )
        self.assertIn("environment: desktop-acceptance", self.text)

    def test_acceptance_environment_must_preexist_with_required_reviewer(self) -> None:
        preflight_start = self.text.index("  acceptance-environment-policy:")
        acceptance_start = self.text.index("  real-user-windows-acceptance:")
        preflight = self.text[preflight_start:acceptance_start]
        acceptance = self.text[acceptance_start:]
        self.assertLess(preflight_start, acceptance_start)
        self.assertIn("runs-on: ubuntu-latest", preflight)
        self.assertNotIn("environment:", preflight)
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/environments/desktop-acceptance"',
            preflight,
        )
        self.assertIn('select(.type == "required_reviewers")', preflight)
        self.assertIn("reviewer_count", preflight)
        self.assertIn("custom_branch_policies", preflight)
        self.assertIn("deployment-branch-policies", preflight)
        self.assertIn("total_policy_count", preflight)
        self.assertIn('select(.name == "main")', preflight)
        self.assertIn("must allow only the main branch", preflight)
        self.assertIn("needs: acceptance-environment-policy", acceptance)

    def test_acceptance_revalidates_environment_after_gate_before_checkout(self) -> None:
        acceptance_start = self.text.index("  real-user-windows-acceptance:")
        acceptance = self.text[acceptance_start:]
        policy_start = acceptance.index(
            "Re-verify desktop-acceptance policy after environment approval"
        )
        checkout_start = acceptance.index("Checkout exact source commit")
        self.assertLess(policy_start, checkout_start)
        policy = acceptance[policy_start:checkout_start]
        self.assertIn("actions: read", acceptance[:policy_start])
        self.assertIn("DIVAN_POLICY_TOKEN: ${{ github.token }}", policy)
        self.assertIn("Bearer $env:DIVAN_POLICY_TOKEN", policy)
        self.assertIn("environments/desktop-acceptance", policy)
        self.assertIn('Where-Object { $_.type -eq "required_reviewers" }', policy)
        self.assertIn("custom_branch_policies", policy)
        self.assertIn("deployment-branch-policies", policy)
        self.assertIn('Where-Object { $_.name -eq "main" }', policy)
        self.assertIn("must still allow only the main branch", policy)
        self.assertNotIn("DIVAN_POLICY_TOKEN", acceptance[checkout_start:])

    def test_acceptance_requires_exact_current_main_source_sha_pin(self) -> None:
        self.assertIn("source_sha:", self.text)
        self.assertIn("required: true", self.text)
        self.assertIn("DIVAN_EXPECTED_SOURCE_SHA: ${{ inputs.source_sha }}", self.text)
        self.assertIn("Verify requested acceptance source identity", self.text)
        self.assertIn("source_sha must be an exact 40-character Git commit SHA", self.text)
        self.assertIn("Acceptance checkout does not match the workflow event source SHA", self.text)
        self.assertIn(
            "Requested acceptance source SHA does not match the workflow source commit",
            self.text,
        )
        self.assertIn("Invoke-RestMethod", self.text)
        self.assertIn("git/ref/heads/main", self.text)
        self.assertIn(
            "main moved after acceptance dispatch; restart acceptance on current main",
            self.text,
        )

    def test_live_main_token_is_scoped_only_to_source_verification_step(self) -> None:
        verify_start = self.text.index("Verify requested acceptance source identity")
        next_step = self.text.index("Resolve acceptance evidence path", verify_start)
        verify = self.text[verify_start:next_step]
        rest = self.text[next_step:]
        self.assertIn("DIVAN_GITHUB_TOKEN: ${{ github.token }}", verify)
        self.assertIn("Bearer $env:DIVAN_GITHUB_TOKEN", verify)
        self.assertNotIn("DIVAN_GITHUB_TOKEN", rest)

    def test_acceptance_runner_uses_dedicated_release_label(self) -> None:
        self.assertIn("divan-desktop-acceptance", self.text)
        self.assertNotIn("runs-on: [self-hosted, windows, x64]\n", self.text)

    def test_acceptance_fails_fast_on_both_real_agent_sessions(self) -> None:
        preflight = PREFLIGHT_SCRIPT.read_text(encoding="utf-8")
        step = "Verify authenticated Codex and Claude sessions before build"
        self.assertIn(step, self.text)
        self.assertIn("python scripts/desktop_agent_preflight.py", self.text)
        self.assertLess(self.text.index(step), self.text.index("Build exact-source NSIS candidate"))
        self.assertIn('shutil.which("codex")', preflight)
        self.assertIn('shutil.which("claude")', preflight)
        self.assertIn('(codex, "login", "status")', preflight)
        self.assertIn('"--permission-mode",\n            "plan"', preflight)
        self.assertIn("scripts/windows_desktop_acceptance.ps1", self.text)
        self.assertIn("--source-commit $sourceCommit", self.text)
        self.assertIn("--source-tree $sourceTree", self.text)
        self.assertIn("$env:RUNNER_TEMP", self.text)

    def test_acceptance_uses_protocol_review_verdict_casing(self) -> None:
        script = ACCEPTANCE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('$review.review.verdict -ne "pass"', script)
        self.assertNotIn('$review.review.verdict -ne "PASS"', script)

    def test_evidence_is_attested_and_uploaded(self) -> None:
        self.assertIn("id-token: write", self.text)
        self.assertIn("attestations: write", self.text)
        self.assertIn("actions/attest-build-provenance@", self.text)
        self.assertIn("name: divan-windows-acceptance", self.text)
        self.assertIn("retention-days: 30", self.text)

    def test_no_release_or_api_secrets_are_exposed_to_acceptance_job(self) -> None:
        preflight = PREFLIGHT_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY", self.text)
        self.assertNotIn("OPENAI_API_KEY", self.text)
        self.assertNotIn("ANTHROPIC_API_KEY", self.text)
        self.assertNotIn("OPENAI_API_KEY", preflight)
        self.assertNotIn("ANTHROPIC_API_KEY", preflight)

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
