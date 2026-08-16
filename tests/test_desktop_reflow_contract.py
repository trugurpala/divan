from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STYLES = ROOT / "apps" / "desktop" / "src" / "styles.css"
TAURI_CONFIG = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"


class DesktopReflowContractTests(unittest.TestCase):
    def test_css_allows_zoom_reflow_without_changing_native_window_floor(self) -> None:
        css = STYLES.read_text(encoding="utf-8")
        config = TAURI_CONFIG.read_text(encoding="utf-8")

        self.assertIn("min-width:320px", css)
        self.assertNotIn("body{margin:0;min-width:1100px", css)
        self.assertIn("@media(max-width:1099px)", css)
        self.assertIn("@media(max-width:700px)", css)
        self.assertIn("grid-row:3", css)
        self.assertIn('"minWidth": 1100', config)

    def test_small_viewport_keeps_primary_content_in_one_column(self) -> None:
        css = STYLES.read_text(encoding="utf-8")

        small = css.split("@media(max-width:700px)", 1)[1]
        self.assertIn(".app-shell{display:block}", small)
        self.assertIn(".summary-grid{grid-template-columns:1fr", small)
        self.assertIn(".pipeline{grid-template-columns:1fr}", small)
        self.assertIn(".action-row{align-items:stretch;flex-direction:column", small)


if __name__ == "__main__":
    unittest.main()
