import copy
import importlib.util
import pathlib
import unittest

KOK = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_candidate_review", KOK / "scripts" / "candidate_review.py"
)
MECLIS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MECLIS)


class MeclisTesti(unittest.TestCase):
    def test_guncel_defter_gecerli(self):
        veri = MECLIS.oku(KOK)
        adaylar = MECLIS.denetle(veri)
        self.assertEqual(len(adaylar), 7)
        self.assertEqual(
            next(aday["decision"] for aday in adaylar if aday["id"] == "punkpeye-awesome-mcp-servers"),
            "REFERENCE",
        )

    def test_project_os_adaylari_sabit_pin_ve_lisans_kanitiyla_kayitli(self):
        veri = MECLIS.oku(KOK)
        adaylar = veri["candidates"]
        beklenen = {
            "agentskills-agentskills": ("ADOPT", "38a2ff82958afee88dadf4831509e6f7e9d8ef4e"),
            "github-spec-kit": ("ADAPT", "cf0abe28f7ee875448f9e4dbd8cd2b533797a1cb"),
            "fission-openspec": ("ADAPT", "a874d1d6715886db9210c527b1fc3799d9688a76"),
            "maxmiksa-auto-company": ("REFERENCE", "ebfab9b4bd5f0ab5ad452a1ff85285b3c141acdd"),
            "googlechrome-lighthouse-ci": ("ADOPT", "ebee453dad3f8acacd657a62ccc65e3296afb7d0"),
            "lycheeverse-lychee": ("ADOPT", "af73b4e02731e0ff3a678b56769704d689138279"),
        }
        self.assertEqual(len({aday["id"] for aday in adaylar}), len(adaylar))
        kayitlar = {aday["id"]: aday for aday in adaylar}
        for kimlik, (karar, pin) in beklenen.items():
            with self.subTest(candidate=kimlik):
                aday = kayitlar[kimlik]
                self.assertEqual(aday["decision"], karar)
                self.assertEqual(aday["reviewed_head"], pin)
                self.assertRegex(aday["reviewed_head"], r"^[0-9a-f]{40}$")
                if aday["decision"] in {"ADOPT", "ADAPT"}:
                    self.assertNotEqual(aday["license"]["spdx"], "UNKNOWN")
                self.assertIn(aday["license"]["evidence_url"], aday["evidence"])
                self.assertEqual(aday["observed_at"], "2026-07-23")
                self.assertEqual(aday["next_review"], "2026-10-23")

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
