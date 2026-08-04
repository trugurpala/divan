import copy
import importlib.util
import pathlib
import unittest
import urllib.error
from unittest import mock

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
        self.assertEqual(len(adaylar), 26)
        self.assertEqual(
            next(aday["decision"] for aday in adaylar if aday["id"] == "punkpeye-awesome-mcp-servers"),
            "REFERENCE",
        )
        ecc = next(aday for aday in adaylar if aday["id"] == "affaan-m-ecc")
        self.assertEqual(
            (ecc["decision"], ecc["reviewed_head"], ecc["license"]["spdx"]),
            ("ADAPT", "0c1d7be9a750627fb2a6534c78a998cc46d03f9c", "MIT"),
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
            "atomantic-portos": ("ADAPT", "94ffc65482f9c24fb44e9b06c728f50cc5829095"),
            "cherryhq-cherry-studio": ("REFERENCE", "f61624e70d9f47ef2548656dd5f9f89666d4ac81"),
            "elij-macher-agent": ("REFERENCE", "73c5619674b902486cdd64aeeb7fe75af5fdcb2f"),
            "jason-0409-g-vivarium": ("REFERENCE", "a915249440e52879bac4013630533d78505e87d1"),
            "josephniel-majordomo": ("REFERENCE", "d41cf2c00d2e25bbd8c2ddc9b3918db17557d7bd"),
            "nmdra-notebrain-cli": ("REFERENCE", "98365b6523892472812a484883bce84a6eefd578"),
            "tinqiao-oss-engramory": ("ADAPT", "9469d79c0445c7238df8ba5e00241beca6532bd6"),
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
                self.assertRegex(aday["observed_at"], r"^2026-07-(23|31)$")
                self.assertRegex(aday["next_review"], r"^2026-10-(23|31)$")

    def test_vibe_ux_adaylari_pinli_ve_lisans_kararli(self):
        adaylar = {aday["id"]: aday for aday in MECLIS.oku(KOK)["candidates"]}
        beklenen = {
            "ibelick-ui-skills": ("ADAPT", "MIT"),
            "addyosmani-agent-skills": ("REFERENCE", "MIT"),
            "emilkowalski-skills": ("ADAPT", "MIT"),
            "ehmo-platform-design-skills": ("REFERENCE", "MIT"),
            "raintree-hig-doctor": ("REFERENCE", "MIT"),
            "meodai-color-expert": ("REFERENCE", "CC-BY-4.0"),
            "microsoft-skills": ("REFERENCE", "MIT"),
            "openai-skills": ("REFERENCE", "LicenseRef-Figma-Beta"),
            "google-stitch-skills": ("REFERENCE", "Apache-2.0"),
            "fabricioctelles-skills": ("REFERENCE", "Apache-2.0"),
            "ramzesenok-ios-accessibility": ("REJECT", "UNKNOWN"),
        }
        self.assertTrue(set(beklenen).issubset(adaylar))
        for kimlik, (karar, lisans) in beklenen.items():
            with self.subTest(candidate=kimlik):
                aday = adaylar[kimlik]
                self.assertEqual(aday["decision"], karar)
                self.assertEqual(aday["license"]["spdx"], lisans)
                self.assertRegex(aday["reviewed_head"], r"^[0-9a-f]{40}$")
                self.assertIn(aday["license"]["evidence_url"], aday["evidence"])

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

    def test_reviewed_head_and_license_evidence_are_bound(self):
        veri = copy.deepcopy(MECLIS.oku(KOK))
        aday = veri["candidates"][0]
        aday["reviewed_head"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "reviewed_head.*kanıtlara bağlanmalı"):
            MECLIS.denetle(veri)

    def test_license_evidence_cannot_leave_the_pinned_canonical_repository(self):
        veri = copy.deepcopy(MECLIS.oku(KOK))
        aday = veri["candidates"][0]
        dis_url = f"https://attacker.example/{aday['reviewed_head']}"
        aday["license"]["evidence_url"] = dis_url
        aday["evidence"].append(dis_url)
        with self.assertRaisesRegex(ValueError, "lisans kanıtı.*kanonik repo"):
            MECLIS.denetle(veri)

    def test_remote_resolution_rejects_missing_commit(self):
        veri = copy.deepcopy(MECLIS.oku(KOK))
        veri["candidates"] = [veri["candidates"][0]]

        def opener(request, timeout):
            raise urllib.error.HTTPError(
                request.full_url, 422, "No commit found", {}, None
            )

        with self.assertRaisesRegex(ValueError, "GitHub commit kanıtı çözümlenemedi"):
            MECLIS.uzak_kanitlari_denetle(veri, opener=opener)

    def test_remote_resolution_checks_commit_and_license_url(self):
        veri = copy.deepcopy(MECLIS.oku(KOK))
        veri["candidates"] = [veri["candidates"][0]]
        istekler = []

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        def opener(request, timeout):
            istekler.append(request)
            return Response()

        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            resolved = MECLIS.uzak_kanitlari_denetle(veri, opener=opener)
        self.assertEqual(resolved, 1)
        self.assertEqual(len(istekler), 2)
        self.assertIn("api.github.com/repos/", istekler[0].full_url)
        self.assertEqual(
            istekler[0].get_header("Authorization"), "Bearer test-token"
        )
        self.assertEqual(
            istekler[1].full_url,
            veri["candidates"][0]["license"]["evidence_url"],
        )
        self.assertIsNone(istekler[1].get_header("Authorization"))

    def test_authenticated_github_request_rejects_redirects(self):
        handler = MECLIS._YonlendirmeYasak()
        request = MECLIS._github_istegi(
            "https://api.github.com/repos/example/repo/commits/" + "a" * 40,
            kimlik_dogrula=True,
        )
        with self.assertRaises(urllib.error.HTTPError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://attacker.example/token",
            )

    def test_candidate_workflow_resolves_remote_provenance(self):
        workflow = (
            KOK / ".github" / "workflows" / "candidate-review.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python scripts/candidate_review.py --resolve", workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)

    def test_katalog_defterden_ayrilmiyor(self):
        beklenen = MECLIS.katalog_uret(MECLIS.oku(KOK))
        gercek = (KOK / "docs" / "Aday-Meclisi.md").read_text(encoding="utf-8")
        self.assertEqual(gercek, beklenen)


if __name__ == "__main__":
    unittest.main()
