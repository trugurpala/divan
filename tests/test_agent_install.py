from __future__ import annotations

import json
import pathlib
import sys
import unittest
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import host_lifecycle  # noqa: E402
import host_profiles  # noqa: E402


class AgentInstallContractTests(unittest.TestCase):
    def test_manifest_has_versioned_machine_contract(self) -> None:
        manifest = json.loads((ROOT / "divan-install.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["supported_hosts"], ["claude", "codex"])
        self.assertEqual(manifest["release_policy"]["resolve"], "latest-immutable-github-release")
        self.assertTrue(manifest["release_policy"]["exclude_draft"])
        self.assertTrue(manifest["release_policy"]["exclude_prerelease"])
        self.assertTrue(manifest["release_policy"]["require_tag"])
        self.assertNotIn("main", manifest["release_policy"]["resolve"])
        self.assertEqual(manifest["commands"]["recovery"], "{recovery_command}")
        required = {
            "status",
            "version",
            "source_ref",
            "source_commit",
            "host",
            "profile",
            "package_count",
            "skill_count",
            "doctor_status",
            "restart_required",
            "next_action",
            "recovery_command",
        }
        self.assertEqual(set(manifest["result_fields"]), required)
        self.assertEqual(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            (ROOT / "divan-install.json").read_text(encoding="utf-8"),
        )

    def test_ready_is_authorized_only_by_healthy_native_doctor(self) -> None:
        native = host_profiles.install_result_fields(
            version="1.3.2",
            source_ref="v1.3.2",
            source_commit="a" * 40,
            host="codex",
            profile="native",
            package_count=5,
            skill_count=42,
            doctor_status="healthy",
            selected_mode=host_profiles.NATIVE_MODE,
            recovery_command="python divan.pyz recover transaction.json",
        )
        self.assertTrue(native["ready"])
        self.assertTrue(native["restart_required"])
        self.assertEqual(native["doctor_status"], "healthy")

        attention = host_profiles.install_result_fields(
            version="1.3.2",
            source_ref="v1.3.2",
            source_commit="a" * 40,
            host="codex",
            profile="native",
            package_count=5,
            skill_count=42,
            doctor_status="attention",
            selected_mode=host_profiles.NATIVE_MODE,
            recovery_command=None,
        )
        self.assertFalse(attention["ready"])
        self.assertNotEqual(attention["doctor_status"], "healthy")

    def test_fallback_never_claims_native_capabilities(self) -> None:
        fallback = host_profiles.install_result_fields(
            version="1.3.2",
            source_ref="v1.3.2",
            source_commit="a" * 40,
            host="codex",
            profile="auto",
            package_count=5,
            skill_count=42,
            doctor_status="not-applicable",
            selected_mode=host_profiles.FALLBACK_MODE,
            recovery_command="powershell.exe -File uninstall_codex.ps1",
        )
        self.assertFalse(fallback["ready"])
        self.assertEqual(fallback["doctor_status"], "not-applicable")
        self.assertFalse(host_profiles.capabilities(host_profiles.FALLBACK_MODE)["commands"])
        self.assertFalse(host_profiles.capabilities(host_profiles.FALLBACK_MODE)["native_lifecycle"])

    def test_standard_fields_are_added_to_preview_records(self) -> None:
        options = SimpleNamespace(
            host="codex",
            profile="native",
            ref="v1.3.2",
        )
        record: dict[str, object] = {"status": "dry-run"}
        host_lifecycle._annotate_result(
            record,
            options,
            ROOT,
            {"sadrazam": {"version": "0.10.0"}},
            host_profiles.NATIVE_MODE,
            "not-run",
        )
        for key in json.loads((ROOT / "divan-install.json").read_text(encoding="utf-8"))["result_fields"]:
            self.assertIn(key, record)
        self.assertFalse(record["ready"])
        self.assertFalse(record["restart_required"])

    def test_agent_docs_and_readmes_explain_restart_and_natural_language(self) -> None:
        guide = (ROOT / "INSTALL_FOR_AGENTS.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(guide.splitlines()), 100)
        self.assertIn("doctor_status", guide)
        self.assertIn("new session", guide)
        self.assertIn("natural language", guide)
        for path in ("README.md", "README.en.md", "README.tr.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("Install Divan from this GitHub repository", content) if path != "README.tr.md" else self.assertIn("Bu GitHub deposundaki Divan'ı", content)
            self.assertIn("READY", content)
            self.assertIn("INSTALL_FOR_AGENTS.md", content)


if __name__ == "__main__":
    unittest.main()
