from __future__ import annotations

import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "github"


def png_size(path: pathlib.Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG: {path}")
    return struct.unpack(">II", payload[16:24])


class VisualSystemTests(unittest.TestCase):
    def test_figma_exports_have_canonical_names_and_dimensions(self) -> None:
        expected = {
            "hero.png": (1600, 640),
            "evidence-flow.png": (1600, 900),
            "social-preview.png": (1280, 640),
            "launch-horizontal.png": (1200, 675),
            "community-square.png": (1200, 1200),
        }
        for name, size in expected.items():
            with self.subTest(name=name):
                path = ASSETS / name
                self.assertEqual(png_size(path), size)
                self.assertLess(path.stat().st_size, 1_000_000)

    def test_muhurdar_svg_is_static_and_safe(self) -> None:
        svg = (ASSETS / "muhurdar-seal.svg").read_text(encoding="utf-8")
        self.assertIn("<svg", svg)
        lowered = svg.lower()
        for forbidden in ("<script", "javascript:", "onload=", "foreignobject"):
            self.assertNotIn(forbidden, lowered)
        self.assertEqual(lowered.count("http://"), 1)  # required SVG namespace only

    def test_figma_source_and_public_surfaces_use_new_assets(self) -> None:
        guide = (ROOT / "docs" / "Gorsel-Sistem.md").read_text(encoding="utf-8")
        self.assertIn("https://www.figma.com/design/Z325Jjy36I7KLdizcaZAnZ", guide)
        for relative in ("README.md", "README.en.md", "README.tr.md"):
            readme = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("docs/assets/github/hero.png", readme)
            self.assertIn("docs/assets/github/evidence-flow.png", readme)
        for relative in ("docs/index.html", "site/index.html"):
            html = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("docs/assets/github/social-preview.png", html)
            self.assertIn("assets/github/muhurdar-seal.svg", html)


if __name__ == "__main__":
    unittest.main()
