from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import plugin_sdk
from divan_runtime.plugin_discovery import load_plugin_candidate


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
            "evidence": "https://github.com/example/playwright-evidence/LICENSE",
        },
        "requires_mandate": False,
    }
    payload.update(overrides)
    return payload


class PluginRejectionContractTests(unittest.TestCase):
    """One negative case per manifest rejection reason.

    A plugin manifest is untrusted third-party input. Every rejection reason is
    a control, and a control with no test can be deleted or loosened without
    anything going red. These cases exist so that cannot happen quietly.
    """

    def assertRejects(self, code: str, payload) -> None:
        result = plugin_sdk.validate_manifest_payload(payload)
        self.assertFalse(result.ok, f"{code} was accepted")
        self.assertIsNone(result.manifest)
        self.assertIn(
            code,
            {issue.code for issue in result.errors},
            f"expected {code}, got {[issue.code for issue in result.errors]}",
        )

    def test_a_valid_manifest_is_still_accepted(self) -> None:
        result = plugin_sdk.validate_manifest_payload(valid_manifest())
        self.assertTrue(result.ok, [issue.code for issue in result.errors])

    def test_root_shape(self) -> None:
        for payload in ([], "manifest", 7, None):
            self.assertRejects("PLUGIN_MANIFEST_ROOT_INVALID", payload)

    def test_version_fields(self) -> None:
        for bad in (2, "1", None, 1.0, True):
            self.assertRejects("PLUGIN_SCHEMA_VERSION_INVALID", valid_manifest(schema_version=bad))
            self.assertRejects("PLUGIN_API_VERSION_INCOMPATIBLE", valid_manifest(api_version=bad))

    def test_identity_fields(self) -> None:
        for bad in ("Playwright_Evidence", "-leading", "UPPER", "", 5, None):
            self.assertRejects("PLUGIN_ID_INVALID", valid_manifest(id=bad))
        for bad in ("", "   ", 5, None):
            self.assertRejects("PLUGIN_DISPLAY_NAME_INVALID", valid_manifest(display_name=bad))
            self.assertRejects("PLUGIN_VERSION_INVALID", valid_manifest(version=bad))

    def test_kind_and_transport(self) -> None:
        for bad in ("wizard", "", None, 3):
            self.assertRejects("PLUGIN_KIND_INVALID", valid_manifest(kind=bad))
            self.assertRejects("PLUGIN_TRANSPORT_INVALID", valid_manifest(transport=bad))

    def test_executable_must_be_a_bare_command_name(self) -> None:
        # This is the only control standing between a manifest and a launcher.
        for bad in (
            "C:/Windows/System32/cmd.exe",
            "/usr/bin/env",
            "../../evil",
            "cmd.exe /c calc",
            "tool && rm -rf .",
            "tool;rm",
            "tool|rm",
            "$(tool)",
            "`tool`",
            "tool\nrm",
            "",
            "   ",
            None,
            5,
            ".",
            "..",
            "CON",
            "con",
            "NUL",
            "com1",
            "LPT9",
        ):
            self.assertRejects("PLUGIN_EXECUTABLE_INVALID", valid_manifest(executable=bad))

    def test_capabilities(self) -> None:
        for bad in ("project.read", None, 5, {}):
            self.assertRejects("PLUGIN_CAPABILITIES_INVALID", valid_manifest(capabilities=bad))
        for bad in (5, None, [], {}):
            self.assertRejects("PLUGIN_CAPABILITY_INVALID", valid_manifest(capabilities=[bad]))
        # Empty and unrecognised strings are both simply not in the allowlist.
        for bad in ("", "   ", "project.delete", "shell.exec"):
            self.assertRejects("PLUGIN_CAPABILITY_UNKNOWN", valid_manifest(capabilities=[bad]))
        self.assertRejects(
            "PLUGIN_CAPABILITY_DUPLICATE",
            valid_manifest(capabilities=["project.read", "project.read"]),
        )

    def test_mandate_flag(self) -> None:
        for bad in ("true", 1, 0, None):
            self.assertRejects(
                "PLUGIN_MANDATE_FLAG_INVALID", valid_manifest(requires_mandate=bad)
            )

    def test_source_object(self) -> None:
        for bad in ({}, {"url": "x", "extra": 1}, "https://example.invalid", None):
            self.assertRejects("PLUGIN_SOURCE_INVALID", valid_manifest(source=bad))
        for bad in ("http://example.invalid", "ftp://example.invalid", "example.invalid", ""):
            self.assertRejects("PLUGIN_SOURCE_URL_INVALID", valid_manifest(source={"url": bad}))

    def test_license_object(self) -> None:
        for bad in ({}, {"spdx_expression": "MIT"}, "MIT", None):
            self.assertRejects("PLUGIN_LICENSE_INVALID", valid_manifest(license=bad))
        for bad in ("", "   ", "MIT;DROP", None, 5):
            self.assertRejects(
                "PLUGIN_LICENSE_EXPRESSION_INVALID",
                valid_manifest(license={"spdx_expression": bad, "evidence": "https://e.invalid/l"}),
            )
        for bad in ("http://e.invalid/l", "not-a-url", "", None):
            self.assertRejects(
                "PLUGIN_LICENSE_EVIDENCE_INVALID",
                valid_manifest(license={"spdx_expression": "MIT", "evidence": bad}),
            )

    def test_unknown_root_field(self) -> None:
        self.assertRejects("PLUGIN_MANIFEST_UNKNOWN_FIELD", valid_manifest(postinstall="curl x"))


class PluginDiscoveryRejectionTests(unittest.TestCase):
    """Manifest loading must fail closed before any content is trusted."""

    def _load(self, path: pathlib.Path):
        return load_plugin_candidate(path)

    def assertLoadRejects(self, code: str, path: pathlib.Path) -> None:
        candidate = self._load(path)
        self.assertIsNone(candidate.validation.manifest, f"{code} produced a manifest")
        self.assertIn(
            code,
            {issue.code for issue in candidate.validation.errors},
            f"expected {code}, got {[i.code for i in candidate.validation.errors]}",
        )

    def test_missing_and_unreadable_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertLoadRejects("PLUGIN_MANIFEST_UNREADABLE", root / "absent.json")
            # A directory is openable as a path but never readable as a manifest.
            self.assertLoadRejects("PLUGIN_MANIFEST_UNREADABLE", root)

    def test_invalid_json_and_non_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            broken = root / "broken.json"
            broken.write_text("{not json", encoding="utf-8")
            self.assertLoadRejects("PLUGIN_MANIFEST_INVALID_JSON", broken)

            binary = root / "binary.json"
            binary.write_bytes(b"\xff\xfe\x00garbage")
            candidate = self._load(binary)
            self.assertIsNone(candidate.validation.manifest)

    def test_non_object_root_is_rejected_after_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "list.json"
            path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            self.assertLoadRejects("PLUGIN_MANIFEST_ROOT_INVALID", path)

    @unittest.skipUnless(os.name == "nt", "Windows symlink contract")
    def test_symlinked_manifest_is_rejected_without_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            real = root / "real.json"
            real.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            link = root / "link.json"
            completed = subprocess.run(
                ["cmd", "/c", "mklink", str(link), str(real)],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 or not link.is_symlink():
                self.skipTest("creating a symlink requires Developer Mode or elevation")
            self.assertLoadRejects("PLUGIN_MANIFEST_SYMLINK_REJECTED", link)


if __name__ == "__main__":
    unittest.main()
