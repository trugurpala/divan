from __future__ import annotations

import importlib.util
import pathlib
import unittest

KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_katalog", KOK / "scripts" / "katalog.py")
assert SPEC and SPEC.loader
KATALOG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(KATALOG)


class KatalogTesti(unittest.TestCase):
    def test_katalog_frontmatterdan_ayrilmiyor(self) -> None:
        beklenen = KATALOG.katalog_uret(KOK)
        gercek = (KOK / "docs" / "Vezir-Katalogu.md").read_text(encoding="utf-8")
        self.assertEqual(gercek, beklenen)

    def test_tum_skiller_ve_cok_satirli_aciklama_gorunur(self) -> None:
        metin = KATALOG.katalog_uret(KOK)
        self.assertEqual(metin.count("| **"), 41)
        self.assertIn("Claude API and Anthropic SDK reference", metin)
        self.assertNotIn("| **claude-api** | /-", metin)


if __name__ == "__main__":
    unittest.main()
