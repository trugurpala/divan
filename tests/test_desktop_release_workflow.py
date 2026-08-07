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
        self.assertIn("TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}", signed)
        self.assertIn("DIVAN_UPDATER_PUBKEY: ${{ secrets.DIVAN_UPDATER_PUBKEY }}", signed)
        self.assertIn("Get-AuthenticodeSignature", signed)
        self.assertIn("*.sig", signed)
        self.assertIn("actions/attest-build-provenance@", signed)

    def test_dispatch_input_is_not_interpolated_inside_shell_script(self) -> None:
        run_blocks = "\n".join(
            line for line in self.text.splitlines() if line.lstrip().startswith("run:")
        )
        self.assertNotIn("${{ inputs.", run_blocks)
        self.assertIn("DIVAN_ACCEPTANCE_INPUT: ${{ inputs.acceptance_evidence }}", self.text)
        self.assertIn("$evidence = $env:DIVAN_ACCEPTANCE_INPUT", self.text)

    def test_acceptance_is_bound_to_exact_release_source_tree(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn("git rev-parse 'HEAD^{tree}'", signed)
        self.assertIn("DIVAN_SOURCE_TREE=$sourceTree", signed)
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
