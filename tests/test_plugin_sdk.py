from __future__ import annotations

import importlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

plugin_sdk = importlib.import_module("divan_runtime.plugin_sdk")
plugin_desktop = importlib.import_module("divan_runtime.plugin_desktop")
PluginDecision = plugin_sdk.PluginDecision


def valid_manifest(**overrides):
    payload = {
        "schema_version": 1,
        "id": "playwright-evidence",
        "display_name": "Playwright Evidence",
        "version": "1.0.0",
        "api_version": 1,
        "kind": "evidence",
        "transport": "sidecar-json-v1",
        "executable": "divan-playwright-evidence",
        "capabilities": ["project.read", "evidence.emit"],
        "source": {"url": "https://github.com/example/playwright-evidence"},
        "license": {
            "spdx_expression": "Apache-2.0",
            "evidence": "https://github.com/example/playwright-evidence/blob/main/LICENSE",
        },
        "requires_mandate": False,
    }
    payload.update(overrides)
    return payload


class PluginManifestTests(unittest.TestCase):
    def test_valid_read_only_manifest_is_accepted(self) -> None:
        result = plugin_sdk.validate_manifest_payload(valid_manifest())
        self.assertTrue(result.ok, result.errors)

    def test_unknown_field_fails_closed(self) -> None:
        payload = valid_manifest()
        payload["magic"] = True
        result = plugin_sdk.validate_manifest_payload(payload)
        self.assertIn(
            "PLUGIN_MANIFEST_UNKNOWN_FIELD", {issue.code for issue in result.errors}
        )

    def test_reserved_divan_authority_is_rejected(self) -> None:
        result = plugin_sdk.validate_manifest_payload(
            valid_manifest(capabilities=["authority.expand"])
        )
        self.assertIn(
            "PLUGIN_CAPABILITY_RESERVED", {issue.code for issue in result.errors}
        )

    def test_reviewer_cannot_request_mutation(self) -> None:
        result = plugin_sdk.validate_manifest_payload(
            valid_manifest(
                kind="reviewer",
                capabilities=["project.read", "project.mutate"],
                requires_mandate=True,
            )
        )
        self.assertIn(
            "PLUGIN_READ_ONLY_KIND_MUTATES", {issue.code for issue in result.errors}
        )

    def test_mutating_engine_requires_mandate(self) -> None:
        result = plugin_sdk.validate_manifest_payload(
            valid_manifest(
                id="docker-engine",
                kind="execution-engine",
                executable="divan-docker-engine",
                capabilities=["project.read", "project.mutate", "process.spawn"],
                requires_mandate=False,
            )
        )
        self.assertIn(
            "PLUGIN_MUTATION_REQUIRES_MANDATE", {issue.code for issue in result.errors}
        )


class PluginApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.executable = self.root / "plugin.bin"
        self.executable.write_bytes(b"plugin-v1")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def locator(self, _name: str) -> str:
        return str(self.executable)

    def candidate(self, payload=None):
        path = self.root / "plugin.json"
        path.write_text(
            json.dumps(payload or valid_manifest(), sort_keys=True),
            encoding="utf-8",
        )
        return path, plugin_sdk.load_plugin_candidate(
            path, executable_locator=self.locator
        )

    def test_discovery_hashes_manifest_and_binary(self) -> None:
        _, candidate = self.candidate()
        self.assertTrue(candidate.available)
        self.assertEqual(len(candidate.manifest_sha256), 64)
        self.assertEqual(len(candidate.executable_sha256 or ""), 64)

    def test_activation_requires_explicit_approval(self) -> None:
        _, candidate = self.candidate()
        result = plugin_sdk.validate_activation(candidate, None)
        self.assertIn(
            "PLUGIN_APPROVAL_REQUIRED", {issue.code for issue in result.errors}
        )

    def test_reference_decision_cannot_activate(self) -> None:
        _, candidate = self.candidate()
        approval = plugin_sdk.approve_candidate(
            candidate, decision=PluginDecision.REFERENCE
        )
        result = plugin_sdk.validate_activation(candidate, approval)
        self.assertIn(
            "PLUGIN_DECISION_NOT_ACTIVE", {issue.code for issue in result.errors}
        )

    def test_manifest_change_invalidates_approval(self) -> None:
        path, candidate = self.candidate()
        approval = plugin_sdk.approve_candidate(
            candidate, decision=PluginDecision.ADAPT
        )
        path.write_text(
            json.dumps(valid_manifest(display_name="Changed"), sort_keys=True),
            encoding="utf-8",
        )
        changed = plugin_sdk.load_plugin_candidate(
            path, executable_locator=self.locator
        )
        result = plugin_sdk.validate_activation(changed, approval)
        self.assertIn(
            "PLUGIN_MANIFEST_CHANGED", {issue.code for issue in result.errors}
        )

    def test_binary_change_invalidates_approval(self) -> None:
        path, candidate = self.candidate()
        approval = plugin_sdk.approve_candidate(
            candidate, decision=PluginDecision.ADOPT
        )
        self.executable.write_bytes(b"plugin-v2")
        changed = plugin_sdk.load_plugin_candidate(
            path, executable_locator=self.locator
        )
        result = plugin_sdk.validate_activation(changed, approval)
        self.assertIn(
            "PLUGIN_EXECUTABLE_CHANGED", {issue.code for issue in result.errors}
        )

    def test_adapt_approval_yields_bounded_activation(self) -> None:
        _, candidate = self.candidate()
        approval = plugin_sdk.approve_candidate(
            candidate, decision=PluginDecision.ADAPT
        )
        result = plugin_sdk.validate_activation(candidate, approval)
        self.assertTrue(result.ok, result.errors)
        assert result.activation is not None
        self.assertEqual(
            result.activation.capabilities, ("evidence.emit", "project.read")
        )


class PluginDesktopInspectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.executable = self.root / "plugin.exe"
        self.executable.write_bytes(b"plugin-v1")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manifest_path(self, payload=None) -> pathlib.Path:
        path = self.root / "plugin.json"
        path.write_text(
            json.dumps(payload or valid_manifest(), sort_keys=True),
            encoding="utf-8",
        )
        return path

    def test_trust_report_is_privacy_bounded_and_never_claims_activation(self) -> None:
        report = plugin_desktop.inspect_plugin_manifest(
            self.manifest_path(),
            executable_locator=lambda _name: str(self.executable),
        )
        serialized = json.dumps(report, sort_keys=True)

        self.assertEqual(report["stage"], "approval-required")
        self.assertTrue(report["validation"]["ok"])
        self.assertFalse(report["activation"]["supported"])
        self.assertEqual(report["artifact"]["manifest_name"], "plugin.json")
        self.assertEqual(report["artifact"]["executable_name"], "plugin.exe")
        self.assertEqual(len(report["artifact"]["manifest_sha256"]), 64)
        self.assertEqual(len(report["artifact"]["executable_sha256"]), 64)
        self.assertNotIn(str(self.root), serialized)

    def test_valid_manifest_without_binary_is_not_ready_for_approval(self) -> None:
        report = plugin_desktop.inspect_plugin_manifest(
            self.manifest_path(),
            executable_locator=lambda _name: None,
        )

        self.assertEqual(report["stage"], "executable-missing")
        self.assertTrue(report["validation"]["ok"])
        self.assertFalse(report["artifact"]["executable_available"])
        self.assertIsNone(report["artifact"]["executable_sha256"])

    def test_invalid_manifest_surfaces_stable_issue_codes(self) -> None:
        path = self.manifest_path(valid_manifest(capabilities=["merge.commit"]))
        report = plugin_desktop.inspect_plugin_manifest(
            path,
            executable_locator=lambda _name: str(self.executable),
        )

        self.assertEqual(report["stage"], "invalid")
        self.assertFalse(report["validation"]["ok"])
        self.assertIsNone(report["manifest"])
        self.assertIn(
            "PLUGIN_CAPABILITY_RESERVED",
            {issue["code"] for issue in report["validation"]["errors"]},
        )


if __name__ == "__main__":
    unittest.main()
