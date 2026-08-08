from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-acceptance-bootstrap.yml"


class DesktopAcceptanceBootstrapWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_bootstrap_is_manual_main_only_and_uses_production_gate(self) -> None:
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn("environment: production-release", self.text)

    def test_bootstrap_requires_explicit_reviewer_identity(self) -> None:
        self.assertIn("reviewer_type:", self.text)
        self.assertIn("reviewer_id:", self.text)
        self.assertIn("reviewer_id must be a positive numeric GitHub user/team ID", self.text)
        self.assertIn("reviewers: [{type: $reviewer_type, id: $reviewer_id}]", self.text)

    def test_bootstrap_revalidates_live_main_and_production_gate_before_admin_mutation(self) -> None:
        source_check = self.text.index("Verify bootstrap still targets current main")
        production_gate = self.text.index(
            "Verify production-release approval cannot be bypassed"
        )
        admin_mutation = self.text.index(
            "Create or reconcile protected desktop-acceptance environment"
        )
        self.assertLess(source_check, production_gate)
        self.assertLess(production_gate, admin_mutation)
        source_block = self.text[source_check:production_gate]
        production_block = self.text[production_gate:admin_mutation]
        self.assertIn("GH_TOKEN: ${{ github.token }}", source_block)
        self.assertIn("git/ref/heads/main", source_block)
        self.assertIn("main moved after bootstrap dispatch; restart on current main", source_block)
        self.assertNotIn("DIVAN_RELEASE_ADMIN_TOKEN", source_block)
        self.assertIn("GH_TOKEN: ${{ github.token }}", production_block)
        self.assertIn("environments/production-release", production_block)
        self.assertIn("can_admins_bypass", production_block)
        self.assertIn("must disallow administrator bypass", production_block)
        self.assertNotIn("DIVAN_RELEASE_ADMIN_TOKEN", production_block)

    def test_bootstrap_is_fail_closed_and_main_restricted(self) -> None:
        self.assertIn("set -euo pipefail", self.text)
        self.assertIn(
            '"repos/$GITHUB_REPOSITORY/environments/desktop-acceptance"',
            self.text,
        )
        self.assertIn("custom_branch_policies: true", self.text)
        self.assertIn("deployment-branch-policies", self.text)
        self.assertIn("-f name=main", self.text)
        self.assertIn("required_rule_count", self.text)
        self.assertIn("reviewer_count", self.text)
        self.assertIn("no alternate approval authority", self.text)
        self.assertIn("prevent_self_review_actual", self.text)
        self.assertIn("prevent_self_review does not match the requested policy", self.text)
        self.assertIn("protected_branches", self.text)
        self.assertIn("must use only custom deployment branch policies", self.text)
        self.assertIn("can_admins_bypass", self.text)
        self.assertIn("desktop-acceptance must disallow administrator bypass", self.text)
        self.assertIn("total_policy_count", self.text)
        self.assertIn("must allow only the main branch policy", self.text)

    def test_bootstrap_verifies_exact_requested_reviewer_authority(self) -> None:
        self.assertIn('select(.type == "required_reviewers")', self.text)
        self.assertIn('.reviewer.id == $reviewer_id', self.text)
        self.assertIn('"$required_rule_count" -ne 1', self.text)
        self.assertIn('"$reviewer_count" -ne 1', self.text)
        self.assertIn('"$reviewer_match" -ne 1', self.text)

    def test_admin_token_is_step_scoped(self) -> None:
        secret_binding = "GH_TOKEN: ${{ secrets.DIVAN_RELEASE_ADMIN_TOKEN }}"
        self.assertEqual(self.text.count(secret_binding), 1)
        job_start = self.text.index("  bootstrap-desktop-acceptance:")
        steps_start = self.text.index("    steps:", job_start)
        self.assertNotIn("secrets.", self.text[job_start:steps_start])
        admin_step = self.text.index("Create or reconcile protected desktop-acceptance environment")
        self.assertNotIn("DIVAN_RELEASE_ADMIN_TOKEN", self.text[:admin_step])

    def test_bootstrap_does_not_receive_agent_or_signing_secrets(self) -> None:
        self.assertNotIn("OPENAI_API_KEY", self.text)
        self.assertNotIn("ANTHROPIC_API_KEY", self.text)
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY", self.text)
        self.assertNotIn("DIVAN_WINDOWS_SIGN_COMMAND", self.text)


if __name__ == "__main__":
    unittest.main()
