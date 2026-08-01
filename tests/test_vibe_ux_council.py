import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class VibeUxCouncilTests(unittest.TestCase):
    def test_brainstorming_accepts_safe_explicit_preauthorization(self) -> None:
        text = (
            ROOT / "plugins" / "core-pack" / "skills" / "brainstorming" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Explicit bounded pre-authorization", text)
        self.assertIn("reversible", text)
        for protected in (
            "publication",
            "release",
            "destructive",
            "secrets",
            "payments",
            "messaging",
            "account or security",
        ):
            self.assertIn(protected, text)

    def test_product_design_audit_has_complete_evidence_contract(self) -> None:
        path = (
            ROOT
            / "plugins"
            / "ui-pack"
            / "skills"
            / "product-design-audit"
            / "SKILL.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        for heading in ("Brief", "Inspect", "Audit", "Prioritize", "Verify"):
            self.assertIn(f"## {heading}", text)
        for contract in (
            "desktop",
            "mobile",
            "severity",
            "evidence",
            "impact",
            "actionable fix",
            "reduced motion",
            "keyboard",
        ):
            self.assertIn(contract, text.lower())
        self.assertIn("at most ten", text.lower())

    def test_product_design_audit_has_truthful_license_metadata(self) -> None:
        plugin = (
            ROOT / "plugins" / "ui-pack" / ".claude-plugin" / "plugin.json"
        ).read_text(encoding="utf-8")
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")

        self.assertIn("product-design-audit", plugin)
        self.assertIn("root MIT", plugin)
        self.assertNotIn("every skill directory", plugin)
        self.assertIn("`product-design-audit`", licenses)
        self.assertIn("repository root MIT license", licenses)

    def test_public_eval_counts_match_the_candidate_contract(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        alias = (ROOT / "README.en.md").read_text(encoding="utf-8")
        turkish = (ROOT / "README.tr.md").read_text(encoding="utf-8")
        self.assertEqual(english, alias)
        self.assertIn("five original skills provide 16 behavioral cases", english)
        self.assertIn("5 özgün skill için 16 davranış vakası", turkish)

    def test_published_history_keeps_the_41_skill_truth(self) -> None:
        blueprint = (ROOT / "BLUEPRINT.md").read_text(encoding="utf-8")
        status = (ROOT / "docs" / "Durum-ve-Yol-Haritasi.md").read_text(
            encoding="utf-8"
        )
        for historical in ("v0.9.0 ✓** 41 skill", "v0.10.3 ✓** 41 skill"):
            self.assertIn(historical, blueprint)
        self.assertIn("5 paket ve 42 beceri", status)
        self.assertIn("v1.3.1 kaynak hattı", status)
        self.assertIn("v1.2.0", status)


if __name__ == "__main__":
    unittest.main()
