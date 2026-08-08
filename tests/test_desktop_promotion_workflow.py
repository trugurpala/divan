from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-promote.yml"


class DesktopPromotionWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_promotion_is_manual_main_only_and_environment_protected(self) -> None:
        self.assertIn("name: Desktop Stable Promotion", self.text)
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("push:", self.text)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn("environment: production-release", self.text)
        self.assertIn("contents: write", self.text)
        self.assertIn("attestations: write", self.text)
        self.assertIn("id-token: write", self.text)
        self.assertIn("cancel-in-progress: false", self.text)

    def test_dispatch_ids_are_mapped_through_environment_not_shell_interpolation(self) -> None:
        self.assertIn(
            "DIVAN_PRODUCTION_READINESS_RUN_ID: ${{ inputs.production_readiness_run_id }}",
            self.text,
        )
        self.assertIn("DIVAN_ACCEPTANCE_RUN_ID: ${{ inputs.acceptance_run_id }}", self.text)
        self.assertIn("DIVAN_CANDIDATE_RUN_ID: ${{ inputs.candidate_run_id }}", self.text)
        run_lines = "\n".join(
            line for line in self.text.splitlines() if line.lstrip().startswith("run:")
        )
        self.assertNotIn("${{ inputs.", run_lines)
        self.assertIn("^[1-9][0-9]*$", self.text)

    def test_readiness_acceptance_and_candidate_are_exact_source_bound_and_attested(self) -> None:
        readiness = self.text.index("Verify exact production readiness run and attestation")
        acceptance = self.text.index("Verify exact real-user acceptance run and attestation")
        candidate = self.text.index("Verify exact signed candidate run and download artifacts")
        guard = self.text.index("Re-establish stable release guard on promotion host")
        self.assertLess(readiness, acceptance)
        self.assertLess(acceptance, candidate)
        self.assertLess(candidate, guard)
        self.assertIn("Desktop Production Readiness", self.text)
        self.assertIn(".github/workflows/desktop-production-readiness.yml", self.text)
        self.assertIn("divan-production-readiness", self.text)
        self.assertIn("production readiness evidence attestation verification failed", self.text)
        self.assertIn(
            '"DIVAN_PRODUCTION_READINESS_EVIDENCE=$evidence"',
            self.text,
        )
        self.assertIn("Desktop Real-User Acceptance", self.text)
        self.assertIn(".github/workflows/desktop-acceptance.yml", self.text)
        self.assertIn("Desktop Stable Candidate", self.text)
        self.assertIn(".github/workflows/desktop-release.yml", self.text)
        self.assertIn('$metadata.event -ne "workflow_dispatch"', self.text)
        self.assertIn('$metadata.conclusion -ne "success"', self.text)
        self.assertIn('$metadata.head_sha -ne $env:DIVAN_SOURCE_COMMIT', self.text)
        self.assertIn("gh attestation verify $evidence", self.text)
        self.assertIn("divan-desktop-signed-candidate", self.text)
        self.assertIn("divan-desktop-updater-e2e", self.text)
        self.assertIn("candidate provenance verification failed", self.text)

    def test_promotion_reestablishes_stable_guard_instead_of_trusting_candidate_status(self) -> None:
        self.assertIn("prepare_desktop_release_config.py", self.text)
        self.assertIn("desktop_release_guard.py", self.text)
        self.assertIn("--stable-release", self.text)
        self.assertIn("DIVAN_PRODUCTION_READINESS_EVIDENCE", self.text)
        self.assertIn("--acceptance-evidence $env:DIVAN_ACCEPTANCE_EVIDENCE", self.text)
        self.assertIn("--updater-e2e-evidence $env:DIVAN_UPDATER_E2E_EVIDENCE", self.text)
        self.assertIn("--source-commit $env:DIVAN_SOURCE_COMMIT", self.text)
        self.assertIn("--source-tree $env:DIVAN_SOURCE_TREE", self.text)

    def test_candidate_is_checked_before_immutable_publication(self) -> None:
        guard = self.text.index("desktop_promotion_guard.py")
        authenticode = self.text.index("Get-AuthenticodeSignature", guard)
        immutable = self.text.index("release_guard.py immutable", authenticode)
        endpoint = self.text.index("production updater endpoint to be pre-staged", immutable)
        publish = self.text.index("Publish or verify immutable Desktop GitHub Release", endpoint)
        self.assertLess(guard, authenticode)
        self.assertLess(authenticode, immutable)
        self.assertLess(immutable, endpoint)
        self.assertLess(endpoint, publish)
        self.assertIn("DIVAN_RELEASE_ADMIN_TOKEN", self.text)
        self.assertIn("immutable-releases", self.text)

    def test_desktop_release_tag_is_namespaced_and_artifact_base_is_exact(self) -> None:
        self.assertIn('$tag = "desktop-v$version"', self.text)
        self.assertIn(
            '$expectedArtifactBase = "https://github.com/$env:GITHUB_REPOSITORY/releases/download/$tag"',
            self.text,
        )
        self.assertIn("DIVAN_UPDATER_ARTIFACT_BASE_URL.TrimEnd('/')", self.text)
        self.assertIn("--verify-tag", self.text)
        self.assertIn('title "Divan Desktop v$env:DIVAN_DESKTOP_VERSION"', self.text)

    def test_release_is_re_downloaded_digest_checked_attested_and_live_url_checked(self) -> None:
        self.assertIn("gh release download $tag", self.text)
        self.assertIn("Get-FileHash", self.text)
        self.assertIn("promotion attestation readback failed", self.text)
        self.assertIn(
            '.github/workflows/desktop-promote.yml" --source-ref refs/heads/main --source-digest $env:DIVAN_SOURCE_COMMIT',
            self.text,
        )
        self.assertIn("live updater artifact URL does not return the promoted installer", self.text)
        self.assertIn("production updater endpoint changed during promotion", self.text)
        self.assertIn("DIVAN_DESKTOP_STABLE_PROMOTION=PASS", self.text)

    def test_main_movement_fails_closed_before_and_after_publication(self) -> None:
        self.assertGreaterEqual(self.text.count("git/ref/heads/main"), 3)
        self.assertIn("main moved after acceptance/candidate selection", self.text)
        self.assertIn("main moved before immutable Desktop promotion", self.text)
        self.assertIn("main moved during promotion", self.text)

    def test_promotion_does_not_receive_private_signing_key(self) -> None:
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY", self.text)
        self.assertNotIn("TAURI_SIGNING_PRIVATE_KEY_PASSWORD", self.text)
        self.assertIn("DIVAN_UPDATER_PUBKEY", self.text)
        self.assertIn("DIVAN_WINDOWS_SIGN_COMMAND", self.text)

    def test_release_notes_record_all_authorizing_runs(self) -> None:
        self.assertIn("Production readiness run: `$env:DIVAN_PRODUCTION_READINESS_RUN_ID`", self.text)
        self.assertIn("Acceptance run: `$env:DIVAN_ACCEPTANCE_RUN_ID`", self.text)
        self.assertIn("Signed candidate run: `$env:DIVAN_CANDIDATE_RUN_ID`", self.text)

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
