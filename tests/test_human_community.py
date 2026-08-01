import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class HumanCommunityContractTests(unittest.TestCase):
    def test_writing_contract_and_adr_are_permanent(self):
        contract = read("docs/Yazim-ve-Uslup.md")
        adr = read(".divan/decisions/0012-insan-odakli-yazi-ve-gorsel-sistem.md")
        for expected in (
            "Her paragraf tek ana fikir taşır",
            "de/da",
            "Hacettepe",
            "Erişim tarihi: 1 Ağustos 2026",
            "https://tdk.gov.tr/icerik/yazim-kurallari/",
        ):
            self.assertIn(expected, contract)
        self.assertIn("docs/Yazim-ve-Uslup.md", adr)
        for path in (
            "AGENTS.md",
            "CLAUDE.md",
            "plugins/sadrazam/skills/sadrazam/SKILL.md",
            "plugins/sadrazam/skills/defterdar/SKILL.md",
            "plugins/core-pack/skills/kural-hazinesi/SKILL.md",
        ):
            self.assertIn("docs/Yazim-ve-Uslup.md", read(path), path)

    def test_readme_information_order_and_language_parity(self):
        english = read("README.md")
        self.assertEqual(english, read("README.en.md"))
        headings = (
            "## What does Divan do?",
            "## What does Divan not do?",
            "## How does it work?",
            "## Which installation should you choose?",
            "## Install with one command",
            "## Your first real task",
            "## What will you see?",
            "## What evidence does Divan produce?",
            "## Modular packages",
            "## Host compatibility and evidence levels",
            "## Security and privacy",
            "## Free for the community",
            "## Join the community",
            "## Contributing",
            "## Roadmap and project documents",
            "## Latest release and verification",
            "## Visual system and Figma source",
            "## License and upstream attribution",
        )
        positions = [english.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        turkish = read("README.tr.md")
        for answer in ("ücretsiz", "Claude Code", "Codex", "Nasıl kurulur?", "İlk gerçek iş"):
            self.assertIn(answer, turkish)

    def test_community_governance_files_exist_and_route_people(self):
        for path, marker in {
            "GOVERNANCE.md": "Decision authority",
            "MAINTAINERS.md": "Maintainer scope",
            "ROADMAP.md": "Published",
            "RELEASE.md": "Rollback",
            "SECURITY.md": "private vulnerability reporting",
            "SUPPORT.md": "Where should I go?",
        }.items():
            self.assertIn(marker, read(path), path)

    def test_all_public_intake_routes_are_structured_forms(self):
        forms = {
            "bug.yml",
            "feature.yml",
            "docs.yml",
            "new-skill.yml",
            "source-candidate.yml",
            "kabul-kaniti.yml",
        }
        directory = ROOT / ".github" / "ISSUE_TEMPLATE"
        self.assertTrue(forms.issubset({path.name for path in directory.glob("*.yml")}))
        self.assertFalse(list(directory.glob("*.md")))
        config = read(".github/ISSUE_TEMPLATE/config.yml")
        self.assertIn("blank_issues_enabled: false", config)
        self.assertIn("security/advisories/new", config)

    def test_progress_records_v130_release_candidate_action(self):
        progress = read(".divan/progress.md")
        self.assertIn("v1.2.0", progress)
        self.assertIn("v1.3.0", progress)
        self.assertEqual(progress.count("## Sıradaki kesin iş"), 1)
        next_action = progress.split("## Sıradaki kesin iş", 1)[1].split("\n## ", 1)[0]
        normalized = " ".join(next_action.split())
        self.assertIn("previous immutable tag untouched", normalized)
        self.assertIn("finishing v1.3.0 through the release path", normalized)
        self.assertIn("open a PR", normalized)
        self.assertIn("merge only green checks", normalized)
        self.assertIn("record the public readback evidence", normalized)


if __name__ == "__main__":
    unittest.main()
