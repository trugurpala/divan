from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-build.yml"
ACCEPTANCE_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-acceptance.yml"
CARGO = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
MAIN = ROOT / "apps" / "desktop" / "src-tauri" / "src" / "main.rs"
APP = ROOT / "apps" / "desktop" / "src" / "App.tsx"
PYINSTALLER_PIN = "pyinstaller==6.21.0"


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
        self.assertIn('$updaterSignaturePath = "$($installer.FullName).sig"', signed)
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

    def test_updater_is_optional_for_beta_and_explicitly_enabled_for_signed_release(self) -> None:
        cargo = CARGO.read_text(encoding="utf-8")
        main = MAIN.read_text(encoding="utf-8")
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn('tauri-plugin-updater = { version = "2", optional = true }', cargo)
        self.assertIn('signed-updater = ["dep:tauri-plugin-updater"]', cargo)
        self.assertIn('#[cfg(feature = "signed-updater")]', main)
        self.assertIn("--features signed-updater", signed)

    def test_desktop_release_ui_requires_explicit_user_action(self) -> None:
        app = APP.read_text(encoding="utf-8")
        main = MAIN.read_text(encoding="utf-8")
        self.assertIn('setActiveTab("releases")', app)
        self.assertIn('invoke<UpdateStatus>("check_for_update")', app)
        self.assertIn('invoke<void>("install_update", { approved: true })', app)
        self.assertIn("window.confirm(", app)
        self.assertIn('features.includes("signed-updater")', app)
        self.assertIn('version: env!("CARGO_PKG_VERSION")', main)
        self.assertIn("if !approved", main)
        self.assertNotIn('invoke<UpdateStatus>("check_for_update")\n      .then', app)

    def test_desktop_operator_can_choose_replaceable_execution_engine(self) -> None:
        app = APP.read_text(encoding="utf-8")
        self.assertIn("const [engine, setEngine]", app)
        self.assertIn("const engines = readiness?.engines ?? []", app)
        self.assertIn("setEngine(event.target.value)", app)
        self.assertIn("engine_id: engine || readiness?.recommended_engine || undefined", app)
        self.assertIn("selected.engine_id || engine || readiness?.recommended_engine", app)
        self.assertIn("Native ve Orca aynı Divan execution contract", app)

    def test_windows_updater_signature_is_paired_with_the_nsis_installer(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn('$updaterSignaturePath = "$($installer.FullName).sig"', signed)
        self.assertIn("Test-Path $updaterSignaturePath", signed)
        self.assertNotIn("$updaterArchive", signed)
        self.assertNotRegex(signed, r"zip\|tar\\\.gz")

    def test_desktop_packager_is_pinned_in_every_windows_release_lane(self) -> None:
        for path in (WORKFLOW, BUILD_WORKFLOW, ACCEPTANCE_WORKFLOW):
            text = path.read_text(encoding="utf-8")
            self.assertIn(PYINSTALLER_PIN, text, path.name)
            self.assertNotRegex(text, r"pip install --disable-pip-version-check pyinstaller(?:\s|$)")

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
