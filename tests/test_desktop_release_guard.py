from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_release_guard.py"
SCRIPTS = str(SCRIPT.parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location("desktop_release_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DesktopReleaseError = MODULE.DesktopReleaseError
inspect_desktop = MODULE.inspect_desktop
require_stable_release = MODULE.require_stable_release
readiness_evidence_path = MODULE._readiness_evidence_path
SOURCE_COMMIT = "a" * 40
SOURCE_TREE = "b" * 40
REVIEW_DIFF = "c" * 64
MERGED_COMMIT = "d" * 40


def _acceptance(version: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 3,
        "product": "Ottoman",
        "version": version,
        "platform": "windows",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "core_source_commit": SOURCE_COMMIT,
        "core_source_tree": SOURCE_TREE,
        "result": "PASS",
        "authenticated_worker": True,
        "worker_agent": "codex",
        "authenticated_reviewer": True,
        "independent_reviewer": True,
        "reviewer": "claude",
        "review_bound_to_diff": True,
        "ff_only_merge": True,
        "task_state": "merged",
        "evidence_kinds": ["execution", "review", "approval"],
        "review_diff_sha256": REVIEW_DIFF,
        "merged_commit_sha": MERGED_COMMIT,
    }
    value.update(overrides)
    return value


def _production_readiness(version: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "status": "pass",
        "product": "Ottoman Desktop",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "version": version,
        "production_environment": "production-release",
        "release_overlay_valid": True,
        "updater_public_key_configured": True,
        "updater_public_key_sha256": "7" * 64,
        "updater_endpoint_https": True,
        "artifact_base_exact_release_tag": True,
        "authenticode_sign_command_usable": True,
        "authenticode_signature_valid": True,
        "authenticode_signer_thumbprint_sha256": "8" * 64,
        "authenticode_certificate_not_after_utc": "2099-01-01T00:00:00Z",
        "tauri_private_key_sign_probe": True,
        "tauri_private_key_password_configured": True,
        "private_signing_material_persisted": False,
        "secret_values_in_evidence": False,
    }
    value.update(overrides)
    return value


def _updater_e2e(version: str, **overrides: object) -> dict[str, object]:
    major, minor, patch = (int(part) for part in version.split("."))
    value: dict[str, object] = {
        "schema_version": 1,
        "status": "pass",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "baseline_version": version,
        "upgraded_version": f"{major}.{minor}.{patch + 1}",
        "recovered_version": f"{major}.{minor}.{patch + 2}",
        "valid_signed_upgrade": True,
        "tampered_signature_rejected": True,
        "forward_signed_recovery": True,
        "downgrade_not_offered": True,
        "signatures_mandatory": True,
        "test_only_insecure_transport": True,
        "production_transport_policy": "https-only",
        "baseline_installer_sha256": "1" * 64,
        "upgrade_installer_sha256": "2" * 64,
        "recovery_installer_sha256": "3" * 64,
        "baseline_signature_sha256": "4" * 64,
        "upgrade_signature_sha256": "5" * 64,
        "recovery_signature_sha256": "6" * 64,
    }
    value.update(overrides)
    return value


def _release_config(path: pathlib.Path) -> None:
    path.write_text(
        json.dumps(
            {
                "bundle": {
                    "createUpdaterArtifacts": True,
                    "windows": {"signCommand": "sign-tool %1"},
                },
                "plugins": {
                    "updater": {
                        "pubkey": "PUBLIC-KEY",
                        "endpoints": ["https://updates.example.test/latest.json"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class DesktopReleaseGuardTests(unittest.TestCase):
    def test_desktop_identity_and_versions_are_aligned(self) -> None:
        report = inspect_desktop(ROOT)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(report["main_binary"], "Ottoman.exe")
        self.assertTrue(report["core_sidecar"])
        self.assertFalse(report["updater_configured"])
        self.assertFalse(report["windows_signing_configured"])
        self.assertIsNone(report["production_readiness_evidence"])
        self.assertIsNone(report["updater_e2e_evidence"])

    def test_stable_release_fails_closed_without_external_release_materials(self) -> None:
        report = inspect_desktop(ROOT)

        with self.assertRaisesRegex(DesktopReleaseError, "stable desktop release blocked"):
            require_stable_release(report, {})

    def test_stable_release_requires_signed_config_private_key_and_exact_bound_real_e2e(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = pathlib.Path(temp)
            release_config = temp_root / "release.json"
            _release_config(release_config)
            readiness = temp_root / "readiness.json"
            readiness.write_text(
                json.dumps(_production_readiness(version)),
                encoding="utf-8",
            )
            acceptance = temp_root / "acceptance.json"
            acceptance.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            updater_e2e = temp_root / "updater-e2e.json"
            updater_e2e.write_text(json.dumps(_updater_e2e(version)), encoding="utf-8")

            report = inspect_desktop(
                ROOT,
                release_config=release_config,
                production_readiness_evidence=readiness,
                acceptance_evidence=acceptance,
                updater_e2e_evidence=updater_e2e,
                expected_source_commit=SOURCE_COMMIT,
                expected_source_tree=SOURCE_TREE,
            )
            ready = require_stable_release(
                report,
                {"TAURI_SIGNING_PRIVATE_KEY": "configured-in-secret-store"},
            )

        self.assertTrue(ready["updater_configured"])
        self.assertTrue(ready["windows_signing_configured"])
        self.assertTrue(ready["production_readiness_evidence"]["verified"])
        self.assertTrue(ready["production_readiness_evidence"]["source_bound"])
        self.assertEqual(
            ready["production_readiness_evidence"]["source_commit"],
            SOURCE_COMMIT,
        )
        self.assertTrue(ready["updater_e2e_evidence"]["verified"])
        self.assertTrue(ready["updater_e2e_evidence"]["source_bound"])
        self.assertEqual(ready["updater_e2e_evidence"]["source_commit"], SOURCE_COMMIT)
        self.assertTrue(ready["acceptance_evidence"]["accepted"])
        self.assertTrue(ready["acceptance_evidence"]["source_bound"])
        self.assertEqual(ready["acceptance_evidence"]["source_commit"], SOURCE_COMMIT)
        self.assertEqual(ready["acceptance_evidence"]["core_source_commit"], SOURCE_COMMIT)
        self.assertEqual(ready["acceptance_evidence"]["review_diff_sha256"], REVIEW_DIFF)
        self.assertEqual(ready["stable_release"], "READY")

    def test_stable_release_requires_production_readiness_even_with_other_evidence(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = pathlib.Path(temp)
            release_config = temp_root / "release.json"
            _release_config(release_config)
            acceptance = temp_root / "acceptance.json"
            acceptance.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            updater_e2e = temp_root / "updater-e2e.json"
            updater_e2e.write_text(json.dumps(_updater_e2e(version)), encoding="utf-8")
            report = inspect_desktop(
                ROOT,
                release_config=release_config,
                acceptance_evidence=acceptance,
                updater_e2e_evidence=updater_e2e,
                expected_source_commit=SOURCE_COMMIT,
                expected_source_tree=SOURCE_TREE,
            )
            with self.assertRaisesRegex(
                DesktopReleaseError,
                "production signing readiness evidence is missing",
            ):
                require_stable_release(
                    report,
                    {"TAURI_SIGNING_PRIVATE_KEY": "configured"},
                )

    def test_stable_release_requires_updater_e2e_even_with_real_acceptance(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = pathlib.Path(temp)
            readiness = temp_root / "readiness.json"
            readiness.write_text(
                json.dumps(_production_readiness(version)),
                encoding="utf-8",
            )
            acceptance = temp_root / "acceptance.json"
            acceptance.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            report = inspect_desktop(
                ROOT,
                production_readiness_evidence=readiness,
                acceptance_evidence=acceptance,
                expected_source_commit=SOURCE_COMMIT,
                expected_source_tree=SOURCE_TREE,
            )
            with self.assertRaisesRegex(DesktopReleaseError, "signed updater E2E evidence is missing"):
                require_stable_release(
                    {
                        **report,
                        "updater_configured": True,
                        "windows_signing_configured": True,
                    },
                    {"TAURI_SIGNING_PRIVATE_KEY": "configured"},
                )

    def test_stable_release_rejects_partially_bound_acceptance_even_if_payload_is_pass(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = pathlib.Path(temp)
            readiness = temp_root / "readiness.json"
            readiness.write_text(
                json.dumps(_production_readiness(version)),
                encoding="utf-8",
            )
            acceptance = temp_root / "acceptance.json"
            acceptance.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            updater_e2e = temp_root / "updater-e2e.json"
            updater_e2e.write_text(json.dumps(_updater_e2e(version)), encoding="utf-8")
            report = inspect_desktop(
                ROOT,
                production_readiness_evidence=readiness,
                acceptance_evidence=acceptance,
                updater_e2e_evidence=updater_e2e,
                expected_source_tree=SOURCE_TREE,
            )
            self.assertFalse(report["acceptance_evidence"]["source_bound"])
            with self.assertRaisesRegex(DesktopReleaseError, "exact release source identity"):
                require_stable_release(
                    {
                        **report,
                        "updater_configured": True,
                        "windows_signing_configured": True,
                    },
                    {"TAURI_SIGNING_PRIVATE_KEY": "configured"},
                )

    def test_production_readiness_evidence_rejects_wrong_source_commit(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "readiness.json"
            evidence.write_text(
                json.dumps(_production_readiness(version)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "release source commit"):
                inspect_desktop(
                    ROOT,
                    production_readiness_evidence=evidence,
                    expected_source_commit="e" * 40,
                    expected_source_tree=SOURCE_TREE,
                )

    def test_production_readiness_rejects_secret_minimization_violation(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "readiness.json"
            evidence.write_text(
                json.dumps(_production_readiness(version, secret_values_in_evidence=True)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "secret_values_in_evidence=False"):
                inspect_desktop(ROOT, production_readiness_evidence=evidence)

    def test_production_readiness_rejects_expired_certificate(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "readiness.json"
            evidence.write_text(
                json.dumps(
                    _production_readiness(
                        version,
                        authenticode_certificate_not_after_utc="2000-01-01T00:00:00Z",
                    )
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "certificate is expired"):
                inspect_desktop(ROOT, production_readiness_evidence=evidence)

    def test_readiness_evidence_env_handoff_is_supported(self) -> None:
        self.assertEqual(
            readiness_evidence_path(None, {"DIVAN_PRODUCTION_READINESS_EVIDENCE": "C:/evidence/readiness.json"}),
            pathlib.Path("C:/evidence/readiness.json"),
        )
        cli = pathlib.Path("explicit.json")
        self.assertEqual(
            readiness_evidence_path(
                cli,
                {"DIVAN_PRODUCTION_READINESS_EVIDENCE": "ignored.json"},
            ),
            cli,
        )
        self.assertIsNone(readiness_evidence_path(None, {}))

    def test_updater_e2e_evidence_rejects_wrong_source_commit(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "updater-e2e.json"
            evidence.write_text(json.dumps(_updater_e2e(version)), encoding="utf-8")
            with self.assertRaisesRegex(DesktopReleaseError, "updater E2E evidence does not match"):
                inspect_desktop(
                    ROOT,
                    updater_e2e_evidence=evidence,
                    expected_source_commit="e" * 40,
                    expected_source_tree=SOURCE_TREE,
                )

    def test_updater_e2e_evidence_rejects_failed_runtime_matrix(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "updater-e2e.json"
            evidence.write_text(
                json.dumps(_updater_e2e(version, tampered_signature_rejected=False)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "tampered_signature_rejected=True"):
                inspect_desktop(ROOT, updater_e2e_evidence=evidence)

    def test_acceptance_evidence_rejects_wrong_source_commit(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            with self.assertRaisesRegex(DesktopReleaseError, "release source commit"):
                inspect_desktop(
                    ROOT,
                    acceptance_evidence=evidence,
                    expected_source_commit="e" * 40,
                    expected_source_tree=SOURCE_TREE,
                )

    def test_acceptance_evidence_rejects_wrong_source_tree(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(json.dumps(_acceptance(version)), encoding="utf-8")
            with self.assertRaisesRegex(DesktopReleaseError, "release source tree"):
                inspect_desktop(
                    ROOT,
                    acceptance_evidence=evidence,
                    expected_source_commit=SOURCE_COMMIT,
                    expected_source_tree="e" * 40,
                )

    def test_acceptance_evidence_rejects_core_from_different_source_identity(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(
                json.dumps(_acceptance(version, core_source_commit="e" * 40)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "installed Ottoman Core"):
                inspect_desktop(ROOT, acceptance_evidence=evidence)

    def test_acceptance_evidence_rejects_same_worker_and_reviewer(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(
                json.dumps(_acceptance(version, reviewer="codex")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "cross-agent"):
                inspect_desktop(ROOT, acceptance_evidence=evidence)

    def test_acceptance_evidence_rejects_review_without_diff_binding(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(
                json.dumps(_acceptance(version, review_bound_to_diff=False)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "review_bound_to_diff"):
                inspect_desktop(ROOT, acceptance_evidence=evidence)

    def test_acceptance_evidence_rejects_malformed_review_hash(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        with tempfile.TemporaryDirectory() as temp:
            evidence = pathlib.Path(temp) / "acceptance.json"
            evidence.write_text(
                json.dumps(_acceptance(version, review_diff_sha256="not-a-sha")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DesktopReleaseError, "review_diff_sha256"):
                inspect_desktop(ROOT, acceptance_evidence=evidence)


if __name__ == "__main__":
    unittest.main()
