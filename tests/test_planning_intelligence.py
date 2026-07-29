from __future__ import annotations

import hashlib
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

    def test_single_security_production_and_release_routes_are_high_risk(self) -> None:
        for intent in (
            "Fix a security vulnerability",
            "Deploy to production",
            "Publish a release",
        ):
            with self.subTest(intent=intent):
                execution = self._plan(
                    intent, host="codex", environment={}
                )["execution_plan"]
                self.assertIn(
                    execution["complexity"]["level"], {"high", "critical"}
                )
                self.assertEqual(
                    execution["model_policy"]["capability_class"], "frontier"
                )

        critical = self._plan(
            "Delete production data after leaked credential rotation",
            host="codex",
            environment={},
        )["execution_plan"]
        self.assertEqual(critical["complexity"]["level"], "critical")
        self.assertEqual(
            critical["model_policy"]["reasoning_effort"], "max"
        )

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

    def test_each_declared_independent_reviewer_owns_a_real_gate(self) -> None:
        for workflow in self.contracts.workflows.values():
            if "independent-reviewer" not in workflow.roles:
                continue
            with self.subTest(workflow=workflow.id):
                route = self._plan(
                    workflow.keywords[0], host="codex", environment={}
                )
                owners = {
                    task["owner_role"]
                    for task in route["execution_plan"]["tasks"]
                    if task["workflow"] == workflow.id
                }
                self.assertIn("independent-reviewer", owners)

    def test_parallel_claim_has_explicit_workstream_lanes_and_join(self) -> None:
        route = self._plan(
            "Fix a security vulnerability, deploy to production and publish a release",
            host="codex",
            environment={},
        )
        execution = route["execution_plan"]

        self.assertEqual(
            execution["orchestration"]["lane"], "bounded-parallel"
        )
        self.assertGreater(
            execution["orchestration"]["max_parallel_workstreams"], 1
        )
        self.assertEqual(
            execution["orchestration"]["workstream_semantics"],
            "dependency-graph-lanes",
        )
        lane_tasks = {
            task_id
            for workstream in execution["workstreams"]
            for task_id in workstream["task_ids"]
        }
        workflow_tasks = {
            task["id"]
            for task in execution["tasks"]
            if task["workflow"] != "integrated-delivery"
        }
        self.assertEqual(lane_tasks, workflow_tasks)
        final = execution["tasks"][-1]
        lane_ends = {
            workstream["task_ids"][-1]
            for workstream in execution["workstreams"]
        }
        self.assertEqual(set(final["depends_on"]), lane_ends)

    def test_task_owners_stay_inside_the_selected_frontend_team(self) -> None:
        route = self._plan(
            "Build a React dashboard UI", host="codex", environment={}
        )

        self.assertNotIn("backend-engineer", route["roles"])
        self.assertTrue(
            all(
                task["owner_role"] in route["roles"]
                for task in route["execution_plan"]["tasks"]
            )
        )

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

    def test_duplicate_monorepo_commands_keep_each_workspace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-plan-monorepo-") as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"private": True, "workspaces": ["apps/*"]}),
                encoding="utf-8",
            )
            (project / "package-lock.json").write_text("{}", encoding="utf-8")
            for name in ("admin", "web"):
                workspace = project / "apps" / name
                workspace.mkdir(parents=True)
                (workspace / "package.json").write_text(
                    json.dumps({"scripts": {"test": "vitest"}}),
                    encoding="utf-8",
                )
            route = engine.plan_intent(
                "Run tests", project, self.contracts, environment={}
            )

        commands = {
            (row["workspace"], tuple(row["argv"]))
            for task in route["execution_plan"]["tasks"]
            for row in task["commands"]
            if row["display"] == "npm run test"
        }
        self.assertEqual(
            commands,
            {
                ("apps/admin", ("npm", "run", "test")),
                ("apps/web", ("npm", "run", "test")),
            },
        )

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

    def test_legacy_goal_restart_is_safe_and_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-goal-") as temporary:
            project = pathlib.Path(temporary)
            intent = "Build and test an API"
            target = "VERIFIED"
            inspection = goals._inspection(project)
            identifier = goals.goal_id(intent, target, inspection)
            spec_root = project / ".divan" / "specs" / identifier
            receipt_path = (
                project / ".divan" / "evidence" / identifier / "receipt.json"
            )
            spec_root.mkdir(parents=True)
            receipt_path.parent.mkdir(parents=True)
            project_types = (
                ", ".join(inspection.get("project_types", [])) or "unclassified"
            )
            artifacts = {
                "spec.md": (
                    f"# Goal {identifier}\n\n## Intent\n\n{intent}\n\n"
                    f"## Target\n\n{target}\n\n## Inspection\n\n"
                    f"Project types: {project_types}.\n"
                ).encode(),
                "plan.md": (
                    f"# Plan for {identifier}\n\n"
                    "1. Confirm the specification and applicable project standards.\n"
                    "2. Implement the smallest authorized change with test-first evidence.\n"
                    f"3. Verify evidence through the `{target}` target.\n\n"
                    "## Discovered commands\n\n"
                    "- No project-native command was discovered.\n"
                ).encode(),
                "tasks.md": (
                    f"# Tasks for {identifier}\n\n"
                    "- [ ] Specify acceptance evidence.\n"
                    "- [ ] Record a failing test or mechanical contract check.\n"
                    "- [ ] Implement the authorized change.\n"
                    "- [ ] Verify and append a phase receipt.\n"
                ).encode(),
            }
            relative_artifacts = {}
            for name, content in artifacts.items():
                (spec_root / name).write_bytes(content)
                relative = f".divan/specs/{identifier}/{name}"
                relative_artifacts[relative] = hashlib.sha256(content).hexdigest()
            receipt_path.write_text(
                json.dumps(
                    receipts.new_receipt(
                        identifier, intent, target, relative_artifacts
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            result = goals.start_goal(project, intent, target, True)

        self.assertEqual(result["status"], "legacy-unchanged")
        self.assertTrue(result["migration_required"])


if __name__ == "__main__":
    unittest.main()
