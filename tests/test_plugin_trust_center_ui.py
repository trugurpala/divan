from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "desktop" / "src" / "App.tsx"
TRUST_CENTER = ROOT / "apps" / "desktop" / "src" / "PluginTrustCenter.tsx"
CAPABILITIES = (
    ROOT
    / "apps"
    / "desktop"
    / "src-tauri"
    / "capabilities"
    / "default.json"
)


class PluginTrustCenterUiTests(unittest.TestCase):
    def test_desktop_has_a_first_class_plugin_trust_destination(self) -> None:
        source = APP.read_text(encoding="utf-8")

        self.assertIn('setActiveTab("plugins")', source)
        self.assertIn(">Eklentiler</button>", source)
        self.assertIn("<PluginTrustCenter", source)
        self.assertIn("<PluginInspectorRail", source)

    def test_manifest_selection_is_explicit_json_only_and_core_backed(self) -> None:
        source = APP.read_text(encoding="utf-8")

        self.assertIn('directory: false', source)
        self.assertIn('multiple: false', source)
        self.assertIn('extensions: ["json"]', source)
        self.assertIn('command: "plugin.inspect"', source)
        self.assertIn('manifest_path: selectedManifest.trim()', source)

    def test_trust_center_never_equates_validation_with_activation(self) -> None:
        source = TRUST_CENTER.read_text(encoding="utf-8")

        self.assertIn('aria-live="polite"', source)
        self.assertIn("Validasyon, approval değildir", source)
        self.assertIn("Bu ekran eklentiyi çalıştırmaz.", source)
        self.assertIn("Persistent owner approval", source)
        self.assertNotIn(">Trusted<", source)

    def test_trust_center_does_not_expand_tauri_permissions(self) -> None:
        capability = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        permissions = set(capability["permissions"])

        self.assertEqual(permissions, {"core:default", "dialog:allow-open"})
        self.assertNotIn("fs:default", permissions)
        self.assertNotIn("http:default", permissions)
        self.assertNotIn("store:default", permissions)

    def test_capabilities_are_explained_in_plain_language(self) -> None:
        source = TRUST_CENTER.read_text(encoding="utf-8")

        for capability in (
            "project.read",
            "project.mutate",
            "git.read",
            "git.mutate",
            "process.spawn",
            "network.outbound",
            "evidence.emit",
        ):
            self.assertIn(f'"{capability}"', source)
        self.assertIn("Değişiklik yapabilir", source)


if __name__ == "__main__":
    unittest.main()
