from __future__ import annotations

import importlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

engine_registry = importlib.import_module("divan_runtime.engine_registry")
orca_engine = importlib.import_module("divan_runtime.orca_engine")
ExecutionAuthority = orca_engine.ExecutionAuthority
OrcaEngine = orca_engine.OrcaEngine
OrcaExecutionDenied = orca_engine.OrcaExecutionDenied
RunnerResult = orca_engine.RunnerResult


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, cwd, timeout):
        self.calls.append(tuple(argv))
        return RunnerResult(0, '{"ok":true}', "")


class OrcaEngineTests(unittest.TestCase):
    def test_status_is_read_only_and_json_normalized(self) -> None:
        runner = FakeRunner()
        result = OrcaEngine(runner=runner).status()
        self.assertTrue(result.ok)
        self.assertEqual(result.payload, {"ok": True})
        self.assertEqual(runner.calls[0], ("orca", "status", "--json"))

    def test_worktree_list_uses_current_ps_command(self) -> None:
        runner = FakeRunner()
        OrcaEngine(runner=runner).worktree_list("id:repo-1")
        self.assertEqual(
            runner.calls[0],
            ("orca", "worktree", "ps", "--repo", "id:repo-1", "--json"),
        )

    def test_mutation_requires_mandate(self) -> None:
        runner = FakeRunner()
        engine = OrcaEngine(runner=runner)
        with self.assertRaises(OrcaExecutionDenied):
            engine.worktree_create(name="fix-login", authority=ExecutionAuthority())
        self.assertEqual(runner.calls, [])

    def test_worktree_create_uses_structured_argv_and_redacts_prompt_in_evidence(self) -> None:
        runner = FakeRunner()
        engine = OrcaEngine(runner=runner)
        result = engine.worktree_create(
            name="fix-login",
            repo_selector="id:repo-1",
            agent="codex",
            prompt="secret task context",
            authority=ExecutionAuthority(execute=True, mandate_id="mandate-123"),
        )
        self.assertIn("secret task context", runner.calls[0])
        self.assertNotIn("secret task context", result.argv)
        self.assertIn("<redacted-prompt>", result.argv)
        self.assertEqual(result.mandate_id, "mandate-123")

    def test_worktree_create_rejects_unknown_setup_mode_before_runner(self) -> None:
        runner = FakeRunner()
        with self.assertRaisesRegex(ValueError, "setup must be run, skip, or inherit"):
            OrcaEngine(runner=runner).worktree_create(
                name="fix-login",
                setup="unsafe-mode",
                authority=ExecutionAuthority(execute=True, mandate_id="mandate-123"),
            )
        self.assertEqual(runner.calls, [])


class DecisionTaxonomyTests(unittest.TestCase):
    def base_engine(self) -> dict:
        return {
            "id": "orca",
            "decision": "ADAPT",
            "status": "candidate",
            "license": {
                "spdx_expression": "MIT",
                "evidence": "https://github.com/stablyai/orca/blob/main/LICENSE",
            },
            "source": {
                "url": "https://github.com/stablyai/orca",
                "pin_policy": "manual",
            },
            "host_compatibility": ["claude", "codex", "standalone"],
            "supported_project_types": ["desktop"],
            "forbidden_project_types": [],
            "quality_profiles": ["internal-app-v1"],
            "installation": {
                "modes": ["sidecar"],
                "removal": "remove sidecar",
                "rollback": "use another engine",
            },
            "escape_plan": {
                "summary": "replaceable",
                "steps": ["disable sidecar"],
            },
            "portability": {"data_portable": True},
            "business_logic_ownership": {
                "owner": "project",
                "notes": "Divan owns core",
            },
            "frontend_replaceability": {
                "replaceable": True,
                "notes": "replaceable",
            },
            "when_unavailable": "fallback",
        }

    def validate(self, engine: dict):
        return engine_registry.validate_registry_payload(
            {"schema_version": 1, "engines": [engine]}, "test"
        )

    def test_reject_is_a_valid_decision(self) -> None:
        engine = self.base_engine()
        engine["decision"] = "REJECT"
        result, code = self.validate(engine)
        self.assertEqual(code, 0, result)

    def test_legacy_fork_is_migrated_to_adapt_plus_fork_mode(self) -> None:
        engine = self.base_engine()
        engine["decision"] = "FORK"
        engine["fork_repository"] = "https://github.com/trugurpala/orca"
        result, code = self.validate(engine)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["warnings"][0]["code"], "ENGINE_DECISION_LEGACY_FORK")

    def test_fork_repository_requires_fork_installation_mode(self) -> None:
        engine = self.base_engine()
        engine["fork_repository"] = "https://github.com/trugurpala/orca"
        result, code = self.validate(engine)
        self.assertEqual(code, 1)
        self.assertIn(
            "ENGINE_FORK_URL_INVALID",
            {row["code"] for row in result["errors"]},
        )


if __name__ == "__main__":
    unittest.main()
