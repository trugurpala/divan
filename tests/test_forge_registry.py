from __future__ import annotations

import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_forge_registry", ROOT / "scripts" / "forge_registry.py"
)
assert SPEC and SPEC.loader
FORGE_REGISTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FORGE_REGISTRY)


class ForgeRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = FORGE_REGISTRY.load_registry()
        self.sources = self.registry["sources"]

    def test_registry_passes_machine_validation(self) -> None:
        self.assertEqual(FORGE_REGISTRY.registry_errors(self.registry), [])

    def test_registry_contains_broad_but_bounded_council(self) -> None:
        self.assertEqual(len(self.sources), 18)
        self.assertEqual(len({source["id"] for source in self.sources}), 18)
        self.assertEqual(len({source["repository"] for source in self.sources}), 18)

    def test_wave_one_application_paths_are_exactly_the_original_three(self) -> None:
        wave_one = {
            source["id"]
            for source in self.sources
            if source["wave"] == 1 and source["kind"] == "application-starter"
        }
        self.assertEqual(
            wave_one,
            {"fastapi-fullstack", "nextbase-supabase", "wave-laravel-cpanel"},
        )

    def test_more_golden_paths_exist_beyond_wave_one(self) -> None:
        golden_paths = {
            source["id"] for source in self.sources if source["decision"] == "GOLDEN_PATH"
        }
        self.assertEqual(len(golden_paths), 11)
        self.assertIn("cookiecutter-django", golden_paths)
        self.assertIn("create-tauri-app", golden_paths)
        self.assertIn("obytes-react-native", golden_paths)
        self.assertIn("roots-sage", golden_paths)

    def test_product_bases_are_separate_from_starters(self) -> None:
        product_bases = {
            source["id"] for source in self.sources if source["decision"] == "PRODUCT_BASE"
        }
        self.assertEqual(
            product_bases,
            {"bagisto-commerce", "chatwoot-support", "formance-ledger"},
        )

    def test_serena_is_a_tool_not_a_vendored_starter(self) -> None:
        serena = next(source for source in self.sources if source["id"] == "serena-code-intelligence")
        self.assertEqual(serena["decision"], "TOOL")
        self.assertEqual(serena["materialization"], "official-tool-install")
        self.assertIsNone(serena["profile"])

    def test_reference_repo_is_not_materialized(self) -> None:
        reference = next(
            source for source in self.sources if source["id"] == "claude-code-best-practice"
        )
        self.assertEqual(reference["decision"], "REFERENCE")
        self.assertEqual(reference["materialization"], "none")
        self.assertEqual(reference["build_evidence"], "not_applicable")

    def test_chatwoot_enterprise_scope_is_explicitly_excluded(self) -> None:
        chatwoot = next(source for source in self.sources if source["id"] == "chatwoot-support")
        self.assertIn("enterprise", chatwoot["license"]["scope_note"].lower())
        self.assertIn("excluded", chatwoot["license"]["scope_note"].lower())

    def test_larament_stays_candidate_until_license_file_and_build_review(self) -> None:
        larament = next(source for source in self.sources if source["id"] == "larament-filament")
        self.assertEqual(larament["status"], "CANDIDATE")
        self.assertEqual(larament["license"]["evidence_path"], "composer.json")
        self.assertEqual(larament["build_evidence"], "not_run")

    def test_no_source_auto_installs_or_claims_unrun_builds(self) -> None:
        self.assertTrue(all(source["auto_install"] is False for source in self.sources))
        materializable = [
            source for source in self.sources if source["decision"] != "REFERENCE"
        ]
        self.assertTrue(all(source["build_evidence"] == "not_run" for source in materializable))

    def test_mutable_ref_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["sources"][0]["reviewed_head"] = "main"
        errors = FORGE_REGISTRY.registry_errors(invalid)
        self.assertTrue(any("reviewed_head" in error for error in errors))

    def test_auto_install_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["sources"][0]["auto_install"] = True
        errors = FORGE_REGISTRY.registry_errors(invalid)
        self.assertTrue(any("auto_install" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
