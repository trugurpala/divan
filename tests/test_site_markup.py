from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    first, second = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (first + 0.05) / (second + 0.05)


class SiteMarkupTests(unittest.TestCase):
    def test_skip_link_and_single_main_landmark_exist(self) -> None:
        for relative in ("docs/index.html", "site/index.html"):
            with self.subTest(relative=relative):
                html = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn('class="skip-link" href="#main-content"', html)
                self.assertEqual(len(re.findall(r"<main\b", html)), 1)
                self.assertEqual(len(re.findall(r"</main>", html)), 1)
                self.assertIn('<main id="main-content" tabindex="-1">', html)
                self.assertIn(".skip-link:focus", html)

    def test_small_coral_text_meets_wcag_aa(self) -> None:
        for relative in ("docs/index.html", "site/index.html"):
            with self.subTest(relative=relative):
                html = (ROOT / relative).read_text(encoding="utf-8")
                coral = re.search(r"--mercan:(#[0-9A-Fa-f]{6})", html)
                night = re.search(r"--gece:(#[0-9A-Fa-f]{6})", html)
                assert coral and night
                self.assertGreaterEqual(_contrast(coral.group(1), night.group(1)), 4.5)


if __name__ == "__main__":
    unittest.main()
