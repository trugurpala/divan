from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"


class DesktopReleaseWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_pull_request_contract_is_secret_free(self) -> None:
        contract_start = self.text.index("  contract:")
        signed_start = self.text.index("  signed-windows-candidate:")
        contract = self.text[contract_start:signed_start]
        self.assertIn("permissions:\n      contents: read", contract)
        self.assertNotIn("secrets.", contract)
        self.assertNotIn("environment:", contract)

    def test_signed_candidate_is_manual_main_only_and_environment_protected(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn(
            "if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'",
            signed,
        )
        self.assertIn("environment: production-release", signed)
        self.assertIn("actions: read", signed)
        self.assertIn("attestations: write", signed)
        self.assertIn("TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}", signed)
        self.assertIn("DIVAN_UPDATER_PUBKEY: ${{ secrets.DIVAN_UPDATER_PUBKEY }}", signed)
        self.assertIn("Get-AuthenticodeSignature", signed)
        self.assertIn("*.sig", signed)
        self.assertIn("actions/attest-build-provenance@", signed)

    def test_dispatch_acceptance_run_id_is_not_interpolated_inside_shell_script(self) -> None:
        run_blocks = "\n".join(
            line for line in self.text.splitlines() if line.lstrip().startswith("run:")
        )
        self.assertNotIn("${{ inputs.", run_blocks)
        self.assertIn("DIVAN_ACCEPTANCE_RUN_ID: ${{ inputs.acceptance_run_id }}", self.text)
        self.assertIn("$runId = $env:DIVAN_ACCEPTANCE_RUN_ID", self.text)
        self.assertNotIn("acceptance_evidence:", self.text)

    def test_acceptance_artifact_is_attested_by_exact_workflow_and_same_main_commit(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn('if ($metadata.name -ne "Desktop Real-User Acceptance")', signed)
        self.assertIn('$metadata.head_branch -ne "main"', signed)
        self.assertIn("$metadata.head_sha -ne $env:GITHUB_SHA", signed)
        self.assertIn("gh run download $runId", signed)
        self.assertIn("--name divan-windows-acceptance", signed)
        self.assertIn("gh attestation verify $evidence", signed)
        self.assertIn(
            '--signer-workflow "$env:GITHUB_REPOSITORY/.github/workflows/desktop-acceptance.yml"',
            signed,
        )
        self.assertIn("--source-ref refs/heads/main", signed)
        self.assertIn("--source-digest $env:GITHUB_SHA", signed)

    def test_acceptance_is_bound_to_exact_release_source_commit_and_tree(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn("git rev-parse HEAD", signed)
        self.assertIn("git rev-parse 'HEAD^{tree}'", signed)
        self.assertIn("DIVAN_SOURCE_COMMIT=$sourceCommit", signed)
        self.assertIn("DIVAN_SOURCE_TREE=$sourceTree", signed)
        self.assertIn("--source-commit $env:DIVAN_SOURCE_COMMIT", signed)
        self.assertIn("--source-tree $env:DIVAN_SOURCE_TREE", signed)
        self.assertIn("--acceptance-evidence $env:DIVAN_ACCEPTANCE_EVIDENCE", signed)

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
