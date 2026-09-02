import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DivanRepositoryHardeningTests(unittest.TestCase):
    def test_process_only_superpowers_docs_are_not_shipped(self):
        self.assertFalse((ROOT / "docs" / "superpowers").exists())

    def test_quality_reference_covers_product_engineering_contract(self):
        reference_root = ROOT / "plugins" / "divan" / "skills" / "quality-review" / "references"
        combined = "\n".join(path.read_text(encoding="utf-8").casefold() for path in sorted(reference_root.glob("*.md")))
        required_terms = (
            "i18n",
            "responsive",
            "accessibility",
            "loading",
            "empty",
            "error",
            "security",
            "performance",
            "observability",
            "dependency",
            "type safety",
            "database",
            "api",
            "network",
            "definition of done",
            "fake ui",
            "fake data",
        )
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_readme_does_not_publish_internal_process_paths(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").casefold()
        self.assertNotIn("docs/superpowers", text)
        self.assertNotIn("agentic workers", text)


if __name__ == "__main__":
    unittest.main()
