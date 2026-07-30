from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDIO = ROOT / "plugins" / "sadrazam" / "divan_runtime" / "studio"


def read(name: str) -> str:
    path = STUDIO / name
    if not path.is_file():
        raise AssertionError(f"{name} is missing")
    return path.read_text(encoding="utf-8")


class SeyirUiTests(unittest.TestCase):
    def test_studio_has_one_main_landmark_and_status_announcer(self) -> None:
        document = read("index.html")

        self.assertEqual(document.count("<main"), 1)
        self.assertIn('aria-live="polite"', document)
        self.assertIn('id="connection-state"', document)
        self.assertIn('id="goal-title"', document)
        self.assertIn('id="current-task"', document)
        self.assertIn('id="next-action"', document)
        self.assertIn('id="technical-details"', document)
        self.assertIn('href="#main-content"', document)

    def test_javascript_uses_fragment_capability_and_safe_dom_rendering(self) -> None:
        script = read("studio.js")

        self.assertIn("window.location.hash.slice(1)", script)
        self.assertNotIn("history.replaceState", script)
        self.assertIn('"X-Divan-Session": token', script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("document.write", script)
        self.assertNotIn("eval(", script)

    def test_ui_supports_small_screens_focus_and_reduced_motion(self) -> None:
        document = read("index.html")
        stylesheet = read("studio.css")

        self.assertIn('name="viewport"', document)
        self.assertIn('lang="en"', document)
        self.assertIn("Connecting to Divan", document)
        self.assertIn(":focus-visible", stylesheet)
        self.assertIn("@media (max-width: 480px)", stylesheet)
        self.assertIn("@media (prefers-reduced-motion: reduce)", stylesheet)
        self.assertIn("color-scheme: light dark", stylesheet)
        dark_block = stylesheet.split(
            "@media (prefers-color-scheme: dark)",
            maxsplit=1,
        )[1]
        self.assertIn(".phase-rail", dark_block)
        self.assertIn("background: var(--surface)", dark_block)

    def test_interface_has_five_named_phases_and_non_color_status_text(self) -> None:
        document = read("index.html")

        for phase in ("FERMAN", "PLAN", "ICRA", "TEFTIS", "YAYIN"):
            with self.subTest(phase=phase):
                self.assertIn(f'data-phase="{phase}"', document)
        self.assertIn('class="phase-state"', document)
        self.assertIn('id="goal-status"', document)


if __name__ == "__main__":
    unittest.main()
