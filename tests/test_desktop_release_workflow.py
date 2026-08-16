from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-build.yml"
ACCEPTANCE_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-acceptance.yml"
PRODUCTION_READINESS_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-production-readiness.yml"
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

    def test_signed_candidate_revalidates_live_main_before_setup(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        verify_start = signed.index("- name: Verify signed candidate source is still current main")
        setup_start = signed.index("- name: Setup Python", verify_start)
        verify = signed[verify_start:setup_start]
        self.assertLess(verify_start, setup_start)
        self.assertIn("DIVAN_GITHUB_TOKEN: ${{ github.token }}", verify)
        self.assertIn("git/ref/heads/main", verify)
        self.assertIn("$liveMain -ne $actual", verify)
        self.assertIn("main moved after stable-candidate dispatch or environment approval", verify)
        self.assertNotIn("secrets.", verify)

    def test_signed_candidate_scopes_tokens_and_signing_secrets_to_required_steps(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        job_env = signed[: signed.index("    steps:")]
        self.assertNotIn("secrets.", job_env)
        self.assertNotIn("GH_TOKEN:", job_env)
        self.assertNotIn("DIVAN_GITHUB_TOKEN:", job_env)

        setup_start = signed.index("- name: Setup Python")
        readiness_start = signed.index("- name: Resolve and verify attested production readiness evidence")
        setup_and_dependencies = signed[setup_start:readiness_start]
        self.assertNotIn("secrets.", setup_and_dependencies)
        self.assertNotIn("GH_TOKEN:", setup_and_dependencies)

        self.assertEqual(signed.count("          GH_TOKEN: ${{ github.token }}"), 2)
        self.assertEqual(signed.count("          DIVAN_GITHUB_TOKEN: ${{ github.token }}"), 1)
        self.assertEqual(
            signed.count("          DIVAN_UPDATER_ENDPOINT: ${{ secrets.DIVAN_UPDATER_ENDPOINT }}"),
            1,
        )
        self.assertEqual(
            signed.count(
                "          DIVAN_UPDATER_ARTIFACT_BASE_URL: ${{ secrets.DIVAN_UPDATER_ARTIFACT_BASE_URL }}"
            ),
            1,
        )
        self.assertEqual(
            signed.count(
                "          DIVAN_WINDOWS_SIGN_COMMAND: ${{ secrets.DIVAN_WINDOWS_SIGN_COMMAND }}"
            ),
            1,
        )
        self.assertEqual(
            signed.count(
                "          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}"
            ),
            1,
        )
        self.assertEqual(
            signed.count(
                "          TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}"
            ),
            1,
        )
        self.assertEqual(
            signed.count("          DIVAN_UPDATER_PUBKEY: ${{ secrets.DIVAN_UPDATER_PUBKEY }}"),
            2,
        )

    def test_signed_candidate_removes_ephemeral_release_config_even_on_failure(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        cleanup_start = signed.index("- name: Remove ephemeral signed release configuration")
        cleanup = signed[cleanup_start:]
        self.assertIn("if: always()", cleanup)
        self.assertIn("Test-Path $env:DIVAN_RELEASE_CONFIG -PathType Leaf", cleanup)
        self.assertIn("Remove-Item -LiteralPath $env:DIVAN_RELEASE_CONFIG -Force", cleanup)

    def test_dispatch_run_ids_are_not_interpolated_inside_shell_script(self) -> None:
        run_blocks = "\n".join(
            line for line in self.text.splitlines() if line.lstrip().startswith("run:")
        )
        self.assertNotIn("${{ inputs.", run_blocks)
        self.assertIn(
            "DIVAN_PRODUCTION_READINESS_RUN_ID: ${{ inputs.production_readiness_run_id }}",
            self.text,
        )
        self.assertIn("DIVAN_ACCEPTANCE_RUN_ID: ${{ inputs.acceptance_run_id }}", self.text)
        self.assertIn("$runId = $env:DIVAN_PRODUCTION_READINESS_RUN_ID", self.text)
        self.assertIn("$runId = $env:DIVAN_ACCEPTANCE_RUN_ID", self.text)
        self.assertNotIn("acceptance_evidence:", self.text)

    def test_production_readiness_artifact_is_attested_by_exact_workflow_and_same_main_commit(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        readiness_start = signed.index("Resolve and verify attested production readiness evidence")
        acceptance_start = signed.index("Resolve and verify attested real-user acceptance evidence")
        readiness = signed[readiness_start:acceptance_start]
        self.assertIn('if ($metadata.name -ne "Desktop Production Readiness")', readiness)
        self.assertIn('$metadata.event -ne "workflow_dispatch"', readiness)
        self.assertIn('$metadata.head_branch -ne "main"', readiness)
        self.assertIn("$metadata.head_sha -ne $env:GITHUB_SHA", readiness)
        self.assertIn("gh run download $runId", readiness)
        self.assertIn("--name divan-production-readiness", readiness)
        self.assertIn("gh attestation verify $evidence", readiness)
        self.assertIn(
            '--signer-workflow "$env:GITHUB_REPOSITORY/.github/workflows/desktop-production-readiness.yml"',
            readiness,
        )
        self.assertIn("--source-ref refs/heads/main", readiness)
        self.assertIn("--source-digest $env:GITHUB_SHA", readiness)
        self.assertIn('if ($payload.status -ne "pass"', readiness)
        self.assertIn("$payload.source_commit -ne $sourceCommit", readiness)
        self.assertIn("$payload.source_tree -ne $sourceTree", readiness)
        self.assertIn("private_signing_material_persisted", readiness)
        self.assertIn("secret_values_in_evidence", readiness)
        self.assertLess(readiness_start, acceptance_start)

    def test_release_contract_tracks_production_readiness_changes(self) -> None:
        self.assertIn('      - ".github/workflows/desktop-production-readiness.yml"', self.text)
        self.assertIn('      - "scripts/windows_desktop_production_readiness.ps1"', self.text)
        self.assertIn('      - "tests/test_desktop_production_readiness_workflow.py"', self.text)
        contract = self.text[self.text.index("  contract:") : self.text.index("  updater-e2e-windows:")]
        self.assertIn("tests.test_desktop_production_readiness_workflow", contract)
        self.assertTrue(PRODUCTION_READINESS_WORKFLOW.exists())

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

    def test_signed_candidate_consumes_exact_run_updater_e2e_evidence(self) -> None:
        signed = self.text[self.text.index("  signed-windows-candidate:") :]
        self.assertIn("Download exact-run signed updater e2e evidence", signed)
        self.assertIn(
            "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1",
            signed,
        )
        self.assertIn("name: divan-desktop-updater-e2e", signed)
        self.assertIn("digest-mismatch: error", signed)
        self.assertIn("Updater e2e artifact must contain exactly one JSON evidence file", signed)
        self.assertIn("DIVAN_UPDATER_E2E_EVIDENCE=$evidence", signed)
        self.assertIn("--updater-e2e-evidence $env:DIVAN_UPDATER_E2E_EVIDENCE", signed)

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
        self.assertIn('invoke<UpdateInstallStatus>("install_update", { approved: true })', app)
        self.assertIn("window.confirm(", app)
        self.assertIn('features.includes("signed-updater")', app)
        self.assertIn('version: env!("CARGO_PKG_VERSION")', main)
        self.assertIn("if !approved", main)
        self.assertNotIn('invoke<UpdateStatus>("check_for_update")\n      .then', app)

    def test_desktop_release_ui_fails_closed_on_unknown_or_stale_update_state(self) -> None:
        app = APP.read_text(encoding="utf-8")
        check_start = app.index("const checkForUpdate = async")
        check_end = app.index("const installUpdate", check_start)
        check_block = app[check_start:check_end]
        self.assertLess(
            check_block.index("setUpdateStatus(null)"),
            check_block.index('invoke<UpdateStatus>("check_for_update")'),
        )
        self.assertIn("setUpdateCheckError(", check_block)
        self.assertIn("Önceki sonuç güvenlik nedeniyle geçersiz sayıldı", check_block)
        self.assertIn("if (shellCaps === null)", app)
        self.assertIn("Build kimliği doğrulanmadan beta veya stable kanal varsayımı yapılmaz", app)
        self.assertIn('checkError\n                ? "Kontrol tamamlanamadı"', app)
        self.assertIn("status?.available && !checkError", app)

    def test_install_update_is_bound_to_the_explicitly_checked_candidate(self) -> None:
        app = APP.read_text(encoding="utf-8")
        main = MAIN.read_text(encoding="utf-8")
        check_start = main.index("async fn check_for_update(")
        check_end = main.index('#[cfg(not(feature = "signed-updater"))]', check_start)
        check_block = main[check_start:check_end]
        install_start = main.index("async fn install_update(", check_end)
        install_end = main.index('#[cfg(not(feature = "signed-updater"))]', install_start)
        install_block = main[install_start:install_end]

        self.assertIn("struct PendingUpdate", main)
        self.assertIn(".manage(PendingUpdate::default())", main)
        self.assertIn("*pending = None;", check_block)
        self.assertLess(check_block.index("*pending = None;"), check_block.index("updater.check()"))
        self.assertIn("*pending = Some(update);", check_block)
        self.assertIn("pending.take()", install_block)
        self.assertIn("no checked update is pending", install_block)
        self.assertIn("download_and_install", install_block)
        self.assertNotIn("updater.check()", install_block)
        self.assertIn('const result = await invoke<UpdateInstallStatus>("install_update"', app)

    def test_desktop_interrupted_execution_requires_explicit_recovery_and_retry(self) -> None:
        app = APP.read_text(encoding="utf-8")
        self.assertIn('command: "task.recover.interrupted"', app)
        self.assertIn("const interruptedExecution", app)
        self.assertIn("Ottoman bu görevi otomatik devam ettirmedi", app)
        self.assertIn("Kesintiyi retry'a hazırla", app)
        self.assertIn('selected.state === "running" && !interruptedExecution', app)
        self.assertIn("approve_execution: true", app)

    def test_desktop_operator_can_choose_replaceable_execution_engine(self) -> None:
        app = APP.read_text(encoding="utf-8")
        self.assertIn("const [engine, setEngine]", app)
        self.assertIn("const availableEngines = readiness?.engines ?? []", app)
        self.assertIn("setEngine(event.target.value)", app)
        self.assertIn("engine_id: operatorEngine || undefined", app)
        self.assertIn("operatorEngine || persistedTaskEngine || readiness?.recommended_engine", app)
        self.assertIn("availableEngines.includes(selected.engine_id)", app)
        self.assertNotIn("setEngine((current) => current || value.recommended_engine", app)
        self.assertIn("Native ve Orca aynı Ottoman execution contract", app)

    def test_desktop_blocks_execution_until_the_selected_agent_is_authenticated(self) -> None:
        app = APP.read_text(encoding="utf-8")
        self.assertIn("const executionAgentReady", app)
        self.assertIn('selectedAgentTool?.available && selectedAgentTool.auth === "connected"', app)
        self.assertIn("const executionStartBlocked", app)
        self.assertIn("disabled={executionStartBlocked}", app)
        self.assertIn("worktree oluşturulmadı", app)

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
