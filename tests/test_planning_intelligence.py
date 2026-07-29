from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import engine, goals, planning, receipts  # noqa: E402


class NizamPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contracts = engine.load_contracts(RUNTIME)

    def _plan(
        self,
        intent: str,
        *,
        host: str | None = None,
        context: int | None = None,
        environment: dict[str, str] | None = None,
    ) -> dict:
        temporary = tempfile.TemporaryDirectory(prefix="divan-plan-")
        self.addCleanup(temporary.cleanup)
        return engine.plan_intent(
            intent,
            pathlib.Path(temporary.name),
            self.contracts,
            host_profile=host,
            context_window=context,
            environment=environment,
        )

    def test_unknown_host_and_context_are_explicit_planning_assumptions(self) -> None:
        execution = self._plan("Add a feature", environment={})["execution_plan"]

        self.assertEqual(execution["host"]["id"], "unknown")
        self.assertEqual(execution["context_budget"]["source"], "fallback")
        self.assertEqual(
            execution["context_budget"]["authority"], "planning-assumption"
        )
        self.assertFalse(
            execution["context_budget"]["verified_product_limit"]
        )
        self.assertEqual(execution["model_policy"]["capability_class"], "economy")
        self.assertIsNone(execution["model_policy"]["host_candidate"])

    def test_codex_frontier_candidate_requires_host_confirmation(self) -> None:
        intent = (
            "Fix a security vulnerability, run tests, publish a release, "
            "deploy it and update documentation"
        )
        first = self._plan(
            intent, host="codex", context=1_050_000, environment={}
        )["execution_plan"]
        second = self._plan(
            intent, host="codex", context=1_050_000, environment={}
        )["execution_plan"]

        self.assertEqual(first, second)
        self.assertIn(first["complexity"]["level"], {"high", "critical"})
        self.assertEqual(first["model_policy"]["capability_class"], "frontier")
        candidate = first["model_policy"]["host_candidate"]
        self.assertEqual(candidate["model"], "gpt-5.6-sol")
        self.assertEqual(
            candidate["availability"], "host-confirmation-required"
        )
        self.assertEqual(first["context_budget"]["source"], "override")
        self.assertFalse(first["context_budget"]["verified_product_limit"])
        self.assertLessEqual(
            first["orchestration"]["max_parallel_workstreams"],
            planning.MAX_PARALLEL_WORKSTREAMS,
        )
        self.assertRegex(first["route_id"], r"^route-[0-9a-f]{16}$")

    def test_environment_hints_never_leak_values_and_conflicts_are_ambiguous(
        self,
    ) -> None:
        secret_path = "C:/Users/example/private"
        intent = (
            "Fix a security vulnerability, run tests, publish a release, "
            "deploy it and update documentation"
        )
        execution = self._plan(
            intent,
            environment={
                "CODEX_HOME": secret_path,
                "CLAUDE_CODE_PLUGIN_ROOT": "D:/secret/plugin",
            },
        )["execution_plan"]

        self.assertEqual(execution["host"]["id"], "ambiguous")
        self.assertEqual(
            execution["host"]["hint_keys"],
            ["CLAUDE_CODE_PLUGIN_ROOT", "CODEX_HOME"],
        )
        serialized = json.dumps(execution)
        self.assertNotIn(secret_path, serialized)
        self.assertNotIn("D:/secret/plugin", serialized)
        self.assertEqual(
            execution["orchestration"]["max_parallel_workstreams"], 1
        )

        with self.assertRaisesRegex(ValueError, "supported host") as error:
            planning.build_execution_plan(
                self._plan(intent, environment={}),
                environment={"DIVAN_HOST": "do-not-print-this-value"},
            )
        self.assertNotIn("do-not-print-this-value", str(error.exception))

    def test_context_override_rejects_bool_and_out_of_range_values(self) -> None:
        for value in (True, 0, 4_096, planning.MAX_CONTEXT_TOKENS + 1):
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, "context window"
            ):
                self._plan("Add a feature", context=value, environment={})

    def test_each_workflow_stage_has_one_task_and_dependencies_are_valid(
        self,
    ) -> None:
        plan = self._plan(
            "Build an API integration and run tests",
            host="codex",
            environment={},
        )
        execution = plan["execution_plan"]
        stage_count = sum(
            len(contract["stages"]) for contract in plan["workflow_contracts"]
        )
        self.assertEqual(len(execution["tasks"]), stage_count + 1)
        task_ids = {task["id"] for task in execution["tasks"]}
        self.assertTrue(
            all(
                dependency in task_ids
                for task in execution["tasks"]
                for dependency in task["depends_on"]
            )
        )
        assigned = [
            task_id
            for sefer in execution["sefers"]
            for task_id in sefer["task_ids"]
        ]
        self.assertEqual(sorted(assigned), sorted(task_ids))

    def test_native_commands_keep_shell_free_argv(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-plan-command-") as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"scripts": {"test": "vitest"}}),
                encoding="utf-8",
            )
            (project / "package-lock.json").write_text("", encoding="utf-8")
            route = engine.plan_intent(
                "Run tests",
                project,
                self.contracts,
                environment={},
            )

        command = route["commands"][0]
        self.assertEqual(command["command"], "npm run test")
        task_commands = [
            row
            for task in route["execution_plan"]["tasks"]
            for row in task["commands"]
            if row["display"] == "npm run test"
        ]
        self.assertTrue(task_commands)
        self.assertEqual(task_commands[0]["argv"], ["npm", "run", "test"])
        self.assertFalse(task_commands[0]["auto_execute"])

    def test_goal_persists_route_and_binds_it_to_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-goal-route-") as temporary:
            project = pathlib.Path(temporary)
            result = goals.start_goal(
                project,
                "Build and test an API",
                "verified",
                True,
                host_profile="codex",
                context_window=128_000,
                environment={},
            )
            spec_root = project / ".divan" / "specs" / result["goal_id"]
            route_path = spec_root / "route.json"
            repeated = goals.start_goal(
                project,
                "Build and test an API",
                "verified",
                True,
                host_profile="codex",
                context_window=128_000,
                environment={},
            )

            self.assertEqual(repeated["status"], "unchanged")
            self.assertEqual(
                sorted(path.name for path in spec_root.iterdir()),
                ["plan.md", "route.json", "spec.md", "tasks.md"],
            )
            route = json.loads(route_path.read_text(encoding="utf-8"))
            self.assertEqual(route["execution_plan"]["host"]["id"], "codex")
            verification = receipts.verify_receipt(project / result["receipt"])
            self.assertTrue(verification["ok"], verification["errors"])
            self.assertIn(
                f".divan/specs/{result['goal_id']}/route.json",
                json.loads(
                    (project / result["receipt"]).read_text(encoding="utf-8")
                )["artifacts"],
            )


if __name__ == "__main__":
    unittest.main()
