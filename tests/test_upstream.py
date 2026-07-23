from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_upstream", ROOT / "scripts" / "upstream_watch.py"
)
assert SPEC and SPEC.loader
UPSTREAM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPSTREAM)


class UpstreamGovernanceTests(unittest.TestCase):
    def test_text_hash_is_stable_across_line_endings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upstream-eol-") as temporary:
            root = pathlib.Path(temporary)
            lf = root / "lf.md"
            crlf = root / "crlf.md"
            lf.write_bytes(b"one\ntwo\n")
            crlf.write_bytes(b"one\r\ntwo\r\n")
            self.assertEqual(UPSTREAM.sha256(lf), UPSTREAM.sha256(crlf))

    def test_tree_inventory_uses_platform_independent_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-upstream-") as temporary:
            root = pathlib.Path(temporary)
            nested = root / "references" / "example.md"
            nested.parent.mkdir(parents=True)
            nested.write_text("example\n", encoding="utf-8")

            inventory = UPSTREAM.imza(root)

        self.assertEqual(list(inventory), ["references/example.md"])

    def test_root_license_is_canonical_and_notice_is_separate(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("MIT License\n\nCopyright (c) 2026 trugurpala\n"))
        self.assertNotIn("Bundled third-party", license_text)
        self.assertIn("THE SOFTWARE IS PROVIDED \"AS IS\"", license_text)
        notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("THIRD_PARTY_LICENSES.md", notice)
        self.assertIn("Anthropic", notice)

    def test_all_detected_drift_has_pinned_review_decisions(self) -> None:
        errors, reviews = UPSTREAM.baseline_errors(ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(len(reviews), 15)
        self.assertEqual({review["decision"] for review in reviews}, {"KEEP"})

    def test_canonical_source_inventory_includes_curated_distributed_sources(self) -> None:
        registry = json.loads(
            (ROOT / "registry/upstream-baselines.json").read_text(encoding="utf-8")
        )
        pins = {source["repository"]: source["reviewed_head"] for source in registry["sources"]}

        self.assertEqual(
            pins["PatrickJS/awesome-cursorrules"],
            "b044f956f021b6e8877f16781bcfc466a6a120e9",
        )
        self.assertEqual(
            pins["muratcankoylan/Agent-Skills-for-Context-Engineering"],
            "c578e85e40fe2bda7c1fec91ff64cf5285434934",
        )
        self.assertNotIn("b044f956f021b6e8877f16781bcfc466a6a120e9", repr(UPSTREAM.KURASYON_KAYNAKLARI))

    def test_unreviewed_or_mutable_baseline_is_rejected(self) -> None:
        invalid = {
            "source": "obra/superpowers",
            "reviewed_head": "main",
            "decision": "PENDING",
            "local_tree_sha256": "not-a-hash",
        }
        errors = UPSTREAM.review_errors(invalid)

        self.assertTrue(any("reviewed_head" in error for error in errors))
        self.assertTrue(any("decision" in error for error in errors))
        self.assertTrue(any("local_tree_sha256" in error for error in errors))

    def test_project_os_research_is_documented_without_distribution_claim(self) -> None:
        upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        sources = {
            "agentskills/agentskills": "38a2ff82958afee88dadf4831509e6f7e9d8ef4e",
            "github/spec-kit": "cf0abe28f7ee875448f9e4dbd8cd2b533797a1cb",
            "Fission-AI/OpenSpec": "a874d1d6715886db9210c527b1fc3799d9688a76",
            "MaxMiksa/Auto-Company": "ebfab9b4bd5f0ab5ad452a1ff85285b3c141acdd",
            "GoogleChrome/lighthouse-ci": "ebee453dad3f8acacd657a62ccc65e3296afb7d0",
            "lycheeverse/lychee": "af73b4e02731e0ff3a678b56769704d689138279",
        }
        for repository, pin in sources.items():
            with self.subTest(repository=repository):
                self.assertIn(repository, upstream)
                self.assertIn(pin, upstream)
                self.assertIn(repository, licenses)
        self.assertIn("kaynak kodu dağıtılmaz", upstream)
        self.assertIn("kaynak kodu dağıtılmaz", licenses)


if __name__ == "__main__":
    unittest.main()
