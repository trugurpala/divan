from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-production-environment-bootstrap.yml"


class DesktopProductionEnvironmentBootstrapWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_bootstrap_is_manual_main_only_and_uses_existing_production_gate(self) -> None:
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn("environment: production-release", self.text)

    def test_bootstrap_has_only_read_only_actions_permission_for_policy_checks(self) -> None:
        job_start = self.text.index("  bootstrap-production-release:")
        steps_start = self.text.index("    steps:", job_start)
        job_header = self.text[job_start:steps_start]
        self.assertIn("actions: read", job_header)
        self.assertNotIn("actions: write", job_header)
        self.assertIn("contents: read", job_header)

    def test_bootstrap_requires_exact_independent_reviewer_identity(self) -> None:
        self.assertIn("reviewer_type:", self.text)
        self.assertIn("reviewer_id:", self.text)
        self.assertIn("reviewer_id must be a positive numeric GitHub user/team ID", self.text)
        self.assertIn('gh api "users/$GITHUB_ACTOR" --jq \'.id\'', self.text)
        self.assertIn("reviewer must be independent from the bootstrap initiator", self.text)
        self.assertIn("reviewers: [{type: $reviewer_type, id: $reviewer_id}]", self.text)
        self.assertIn('.reviewer.id == $reviewer_id', self.text)

    def test_admin_token_is_not_exposed_before_source_and_migration_gate_checks(self) -> None:
        source_check = self.text.index("Verify bootstrap still targets current main")
        migration_gate = self.text.index(
            "Verify production-release migration gate exists before admin mutation"
        )
        admin_mutation = self.text.index("Reconcile protected production-release environment")
        self.assertLess(source_check, migration_gate)
        self.assertLess(migration_gate, admin_mutation)
        self.assertNotIn("DIVAN_RELEASE_ADMIN_TOKEN", self.text[:admin_mutation])
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.text[source_check:admin_mutation])
        self.assertIn("git/ref/heads/main", self.text[source_check:migration_gate])
        self.assertIn("single-reviewer migration gate", self.text[migration_gate:admin_mutation])
        self.assertIn("allow only main", self.text[migration_gate:admin_mutation])

    def test_bootstrap_reconciles_self_review_reviewer_and_main_only_policy(self) -> None:
        admin_step = self.text.index("Reconcile protected production-release environment")
        block = self.text[admin_step:]
        self.assertIn("GH_TOKEN: ${{ secrets.DIVAN_RELEASE_ADMIN_TOKEN }}", block)
        self.assertIn("prevent_self_review: true", block)
        self.assertIn("custom_branch_policies: true", block)
        self.assertIn("--method DELETE", block)
        self.assertIn("deployment-branch-policies/$policy_id", block)
        self.assertIn("-f name=main", block)
        self.assertIn("reviewer_match", block)
        self.assertIn("exactly the requested required reviewer", block)
        self.assertIn("total_policy_count", block)
        self.assertIn("must allow only the main branch policy", block)

    def test_bootstrap_fails_closed_until_admin_bypass_is_disabled(self) -> None:
        self.assertIn("can_admins_bypass", self.text)
        self.assertIn('"$can_admins_bypass" != "false"', self.text)
        self.assertIn("still allows administrator bypass", self.text)
        self.assertIn(
            "disable 'Allow administrators to bypass configured protection rules'",
            self.text,
        )

    def test_admin_token_and_release_secrets_remain_minimally_scoped(self) -> None:
        secret_binding = "GH_TOKEN: ${{ secrets.DIVAN_RELEASE_ADMIN_TOKEN }}"
        self.assertEqual(self.text.count(secret_binding), 1)
        job_start = self.text.index("  bootstrap-production-release:")
        steps_start = self.text.index("    steps:", job_start)
        self.assertNotIn("secrets.", self.text[job_start:steps_start])
        self.assertNotIn("OPENAI_API_KEY", self.text)
        self.assertNotIn("ANTHROPIC_API_KEY", self.text)
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY", self.text)
        self.assertNotIn("DIVAN_WINDOWS_SIGN_COMMAND", self.text)
        self.assertNotIn("DIVAN_UPDATER_PUBKEY", self.text)


if __name__ == "__main__":
    unittest.main()
