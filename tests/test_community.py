from __future__ import annotations

import pathlib
import re
import unittest
from html import unescape

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/trugurpala/divan"
DISCUSSIONS_QA = f"{REPOSITORY}/discussions/categories/q-a"
BUG_FORM = f"{REPOSITORY}/issues/new?template=hata.md"
PRIVATE_ADVISORY = f"{REPOSITORY}/security/advisories/new"
CANDIDATE_FORM = f"{REPOSITORY}/issues/new?template=kaynak-adayi.yml"
SKILL_FORM = f"{REPOSITORY}/issues/new?template=yeni-vezir.md"
ACCEPTANCE_FORM = f"{REPOSITORY}/issues/new?template=kabul-kaniti.yml"
PAGES_URL = "https://trugurpala.github.io/divan/"
ROLLBACK_COMMAND = (
    'python scripts/divan.py recover '
    '"C:\\Users\\you\\.divan\\transactions\\upgrade-20260721-120000.json"'
)
UNINSTALL_COMMAND = (
    'python scripts/divan.py recover '
    '"C:\\Users\\you\\.divan\\transactions\\install-20260721-120000.json"'
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class CommunityContractTests(unittest.TestCase):
    def test_contribution_guides_are_bilingual_and_link_support(self) -> None:
        turkish = read("CONTRIBUTING.tr.md")
        english = read("CONTRIBUTING.md")
        self.assertIn("[English](CONTRIBUTING.en.md)", turkish)
        self.assertIn("[Türkçe](CONTRIBUTING.tr.md)", english)
        for guide in (turkish, english):
            self.assertIn("SUPPORT.md", guide)
            self.assertIn("python scripts/validate.py", guide)
            self.assertIn("plugins/<paket>/skills/<skill-adi>/SKILL.md", guide)
            self.assertIn("name", guide)
            self.assertIn("description", guide)
            self.assertIn("64", guide)
            self.assertIn("1024", guide)
            self.assertIn("python scripts/catalog.py --check", guide)
            self.assertIn("python scripts/candidate_review.py --check", guide)
            self.assertRegex(guide, r"ADOPT|adoption")

    def test_support_routes_each_request_to_one_exact_destination(self) -> None:
        support = read("SUPPORT.md")
        for route in (
            DISCUSSIONS_QA,
            BUG_FORM,
            PRIVATE_ADVISORY,
            CANDIDATE_FORM,
            SKILL_FORM,
            ACCEPTANCE_FORM,
        ):
            with self.subTest(route=route):
                self.assertEqual(support.count(route), 1)
        self.assertNotIn("mailto:", support.lower())
        self.assertNotRegex(support.lower(), r"\b(sla|response time|yanıt süresi)\b")
        self.assertIn("Türkçe", support)
        self.assertIn("English", support)

    def test_blank_issues_are_disabled_and_support_links_are_visible(self) -> None:
        config = read(".github/ISSUE_TEMPLATE/config.yml")
        self.assertIn("blank_issues_enabled: false", config)
        self.assertEqual(config.count(f"url: {DISCUSSIONS_QA}"), 1)
        self.assertEqual(config.count(f"url: {PRIVATE_ADVISORY}"), 1)

    def test_quick_path_has_exact_lifecycle_commands(self) -> None:
        version = read("VERSION").strip()
        commands = (
            f"python scripts/divan.py install --host both --ref v{version}",
            f"python scripts/divan.py install --host both --ref v{version} --execute",
            f"python scripts/divan.py doctor --host both --ref v{version}",
            f"python scripts/divan.py update --host both --ref v{version}",
            f"python scripts/divan.py update --host both --ref v{version} --execute",
            ROLLBACK_COMMAND,
            UNINSTALL_COMMAND,
        )
        for relative in ("README.md", "README.en.md", "docs/Hizli-Baslangic.md"):
            content = read(relative)
            with self.subTest(relative=relative):
                for command in commands:
                    self.assertIn(command, content)
                self.assertIn("docs/Kaldirma.md", content)
                self.assertNotRegex(content, r"--rollback-transaction\s+<[^>]+>")

    def test_public_surfaces_link_standards_and_state_v1_truthfully(self) -> None:
        for relative in ("README.md", "README.en.md", "docs/Home.md", "docs/SSS.md"):
            content = read(relative)
            with self.subTest(relative=relative):
                self.assertRegex(content, r"Topluluk-Standartlari(?:\.md)?")
                self.assertIn("7/8", content)
                self.assertRegex(content.lower(), r"not (?:a )?(?:model|runtime)|model veya.*runtime|model.*runtime.*değildir")

    def test_wiki_and_release_manifests_cover_community_surfaces(self) -> None:
        wiki = read("wiki-pages.json")
        manifest = read("release-manifest.json")
        self.assertIn('"slug": "Topluluk-Standartlari"', wiki)
        for path in (
            "SUPPORT.md",
            "CONTRIBUTING.md",
            "CONTRIBUTING.en.md",
            ".github/ISSUE_TEMPLATE/config.yml",
            "docs/Topluluk-Standartlari.md",
            "docs/Hizli-Baslangic.md",
            "docs/Kaldirma.md",
            "docs/Standartlar-ve-Limitler.md",
            "docs/SSS.md",
            "wiki-pages.json",
        ):
            self.assertIn(f'"path": "{path}"', manifest)

    def test_public_contract_distinguishes_distribution_and_installed_project(self) -> None:
        english = read("docs/Project-OS.md")
        turkish = read("docs/Project-OS.tr.md")
        standards = read("docs/Topluluk-Standartlari.md")
        for content in (english, turkish, standards):
            self.assertIn("DCS-", content)
            self.assertIn("DPS-", content)
            self.assertIn("Project OS", content)
        self.assertIn("repository distribution", english)
        self.assertIn("kurulu proje", turkish)
        self.assertIn("supervised", english.lower())
        self.assertIn("gözetimli", turkish.lower())

    def test_project_os_surfaces_are_synchronized_in_wiki_and_release_manifest(self) -> None:
        wiki = read("wiki-pages.json")
        manifest = read("release-manifest.json")
        self.assertIn('"source": "docs/Project-OS.tr.md"', wiki)
        self.assertIn('"slug": "Project-OS"', wiki)
        for path in (
            "docs/Project-OS.md",
            "docs/Project-OS.tr.md",
            "registry/project-standards.json",
            "registry/seo-policy.json",
            "scripts/seo.py",
            "scripts/seo_cli.py",
            "scripts/seo_provider.py",
            "docs/robots.txt",
            "docs/sitemap.xml",
            "site/robots.txt",
            "site/sitemap.xml",
        ):
            self.assertIn(f'"path": "{path}"', manifest)

    def test_readmes_and_company_guides_explain_the_installed_project_path(self) -> None:
        for relative in (
            "README.md",
            "README.tr.md",
            "docs/Company-OS.md",
            "docs/Company-OS.tr.md",
        ):
            content = read(relative)
            with self.subTest(relative=relative):
                self.assertIn("scripts/divan.py init", content)
                self.assertIn("scripts/divan.py audit", content)
                self.assertIn("docs/Project-OS", content)

    def test_both_html_sources_share_homepage_and_lifecycle_contract(self) -> None:
        version = read("VERSION").strip()
        critical = (
            f"python scripts/divan.py install --host both --ref v{version}",
            f"python scripts/divan.py install --host both --ref v{version} --execute",
            f"python scripts/divan.py doctor --host both --ref v{version}",
            f"python scripts/divan.py update --host both --ref v{version}",
            f"python scripts/divan.py update --host both --ref v{version} --execute",
            ROLLBACK_COMMAND,
            UNINSTALL_COMMAND,
        )
        sources = [read(path) for path in ("docs/index.html", "site/index.html")]
        self.assertEqual(sources[0], sources[1])
        for html in sources:
            self.assertIn(f'<link rel="canonical" href="{PAGES_URL}">', html)
            self.assertIn('data-homepage="https://trugurpala.github.io/divan/"', html)
            self.assertIn("Yerel skill/plugin dağıtımı", html)
            self.assertIn("model veya runtime değildir", html)
            self.assertIn("v1: 7/8", html)
            self.assertIn("Topluluk Standartları", html)
            visible = unescape(html)
            self.assertNotRegex(visible, r"--rollback-transaction\s+<[^>]+>")
            for command in critical:
                self.assertEqual(
                    len(re.findall(re.escape(command) + r"(?:</code>|\n)", visible)),
                    1,
                )
            self.assertIn("docs/Kaldirma.md", html)


if __name__ == "__main__":
    unittest.main()
