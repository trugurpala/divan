import copy
import importlib.util
import pathlib
import unittest


KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_meclis", KOK / "scripts" / "meclis.py")
MECLIS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MECLIS)


class MeclisTesti(unittest.TestCase):
    def test_guncel_defter_gecerli(self):
        veri = MECLIS.oku(KOK)
        adaylar = MECLIS.denetle(veri)
        self.assertEqual(len(adaylar), 1)
        self.assertEqual(adaylar[0]["decision"], "REFERENCE")

    def test_mukerrer_url_reddedilir(self):
        veri = MECLIS.oku(KOK)
        veri = copy.deepcopy(veri)
        kopya = copy.deepcopy(veri["candidates"][0])
        kopya["id"] = "baska-kimlik"
        veri["candidates"].append(kopya)
        with self.assertRaisesRegex(ValueError, "yinelenen aday URL"):
            MECLIS.denetle(veri)

    def test_lisanssiz_adopt_reddedilir(self):
        veri = copy.deepcopy(MECLIS.oku(KOK))
        aday = veri["candidates"][0]
        aday["decision"] = "ADOPT"
        aday["status"] = "accepted"
        aday["license"]["spdx"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "lisansı belirsiz"):
            MECLIS.denetle(veri)

    def test_katalog_defterden_ayrilmiyor(self):
        beklenen = MECLIS.katalog_uret(MECLIS.oku(KOK))
        gercek = (KOK / "docs" / "Aday-Meclisi.md").read_text(encoding="utf-8")
        self.assertEqual(gercek, beklenen)


if __name__ == "__main__":
    unittest.main()
