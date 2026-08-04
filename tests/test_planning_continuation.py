from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import engine, goals, planning, receipts  # noqa: E402


class PlanContinuationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contracts = engine.load_contracts(RUNTIME)

    def _project(self) -> pathlib.Path:
        temporary = tempfile.TemporaryDirectory(prefix="divan-continuation-")
        self.addCleanup(temporary.cleanup)
        project = pathlib.Path(temporary.name)
        (project / "package.json").write_text(
            json.dumps({"scripts": {"test": "vitest run"}}) + "\n",
            encoding="utf-8",
        )
        (project / "package-lock.json").write_text("{}\n", encoding="utf-8")
        (project / "pyproject.toml").write_text(
            "[project]\nname = \"continuation-fixture\"\nversion = \"0.0.0\"\n",
            encoding="utf-8",
        )
        return project

    def _plan(
        self,
        project: pathlib.Path,
        intent: str,
        *,
        environment: dict[str, str] | None = None,
    ) -> dict:
        return engine.plan_intent(
            intent,
            project,
            self.contracts,
            host_profile="codex",
            environment={} if environment is None else environment,
        )

    @staticmethod
    def _expected_route_id(execution: dict) -> str:
        unsigned = {
            key: value for key, value in execution.items() if key != "route_id"
        }
        encoded = json.dumps(
            unsigned,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return f"route-{hashlib.sha256(encoded).hexdigest()[:16]}"

    def test_three_route_classes_have_deterministic_bound_continuations(
        self,
    ) -> None:
        project = self._project()
        intents = (
            "Build a small API feature",
            "Fix a failing authentication test",
            (
                "Fix a security vulnerability, deploy to production "
                "and publish a release"
            ),
        )
        for intent in intents:
            with self.subTest(intent=intent):
                plans = [self._plan(project, intent) for _ in range(3)]
                serialized = {
                    json.dumps(
                        plan["execution_plan"]["continuation"],
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    for plan in plans
                }
                self.assertEqual(len(serialized), 1)
                execution = plans[0]["execution_plan"]
                continuation = execution["continuation"]
                ready = sorted(
                    task["id"]
                    for task in execution["tasks"]
                    if not task["depends_on"]
                )
                task = continuation["task"]
                expected = next(
                    row for row in execution["tasks"] if row["id"] == ready[0]
                )
                self.assertEqual(continuation["ready_task_ids"], ready)
                self.assertEqual(task["id"], ready[0])
                for key in (
                    "workflow",
                    "stage",
                    "owner_role",
                    "depends_on",
                    "required_evidence",
                ):
                    self.assertEqual(task[key], expected[key])
                self.assertEqual(
                    execution["route_id"],
                    self._expected_route_id(execution),
                )

    def test_executable_and_manual_checks_are_separate_and_never_automatic(
        self,
    ) -> None:
        execution = self._plan(
            self._project(), "Run tests and improve coverage"
        )["execution_plan"]
        continuation = execution["continuation"]
        task = continuation["task"]

        self.assertFalse(continuation["auto_execute"])
        self.assertEqual(
            continuation["execution_authority"], "not-granted"
        )
        self.assertTrue(task["commands"])
        self.assertTrue(task["manual_checks"])
        for command in task["commands"]:
            self.assertIsInstance(command["argv"], list)
            self.assertTrue(command["argv"])
            self.assertFalse(command["shell"])
            self.assertFalse(command["auto_execute"])
        self.assertTrue(
            all(isinstance(check, str) for check in task["manual_checks"])
        )

    def test_continuation_does_not_capture_environment_values(self) -> None:
        secret_path = "C:/Users/example/private-token-value"
        execution = self._plan(
            self._project(),
            "Fix a security vulnerability",
            environment={"CODEX_HOME": secret_path},
        )["execution_plan"]

        self.assertNotIn(
            secret_path,
            json.dumps(execution["continuation"], ensure_ascii=False),
        )
        self.assertEqual(
            execution["continuation"]["execution_authority"],
            "not-granted",
        )

    def test_legacy_route_match_requires_its_original_route_id(self) -> None:
        current = self._plan(self._project(), "Build and test an API")
        legacy = json.loads(json.dumps(current))
        legacy_execution = legacy["execution_plan"]
        legacy_execution.pop("continuation")
        legacy_execution["route_id"] = self._expected_route_id(legacy_execution)
        self.assertTrue(
            planning._pre_continuation_route_matches(legacy, current)
        )

        for invalid_route_id in (None, "route-" + "0" * 16):
            with self.subTest(route_id=invalid_route_id):
                invalid = json.loads(json.dumps(legacy))
                if invalid_route_id is None:
                    invalid["execution_plan"].pop("route_id")
                else:
                    invalid["execution_plan"]["route_id"] = invalid_route_id
                self.assertFalse(
                    planning._pre_continuation_route_matches(invalid, current)
                )
        malformed = json.loads(json.dumps(legacy))
        malformed["execution_plan"] = list(
            malformed["execution_plan"].items()
        )
        self.assertFalse(
            planning._pre_continuation_route_matches(malformed, current)
        )

    def test_legacy_route_less_restart_rejects_route_directory(self) -> None:
        project = self._project()
        identifier = "goal-0123456789ab"
        spec_root, _, receipt_path = goals._goal_paths(project, identifier)
        spec_root.mkdir(parents=True)
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_text(
            json.dumps(
                {
                    "intent": "Build and test an API",
                    "target": "VERIFIED",
                    "artifacts": {
                        f".divan/specs/{identifier}/{name}": "unused"
                        for name in ("spec.md", "plan.md", "tasks.md")
                    },
                }
            ),
            encoding="utf-8",
        )
        (spec_root / "route.json").mkdir()

        with mock.patch.object(
            receipts, "verify_receipt", return_value={"ok": True}
        ):
            self.assertFalse(
                goals._legacy_goal_is_unchanged(
                    project,
                    spec_root,
                    receipt_path,
                    identifier,
                    "Build and test an API",
                    "VERIFIED",
                    {},
                    {},
                    True,
                )
            )

    def test_pre_continuation_route_restart_is_legacy_unchanged(self) -> None:
        project = self._project()
        intent = "Build and test an API"
        target = "VERIFIED"
        context_window = 128_000
        old_route = goals._goal_route(
            project, intent, target, "codex", context_window, {}
        )
        execution = old_route["execution_plan"]
        execution.pop("continuation")
        execution["route_id"] = self._expected_route_id(execution)
        inspection = goals._inspection(project)
        identity = goals._planning_identity(
            old_route, "codex", context_window, {}
        )
        identifier = goals.goal_id(intent, target, inspection, identity)
        artifacts = goals._artifact_values(
            identifier, intent, target, inspection, old_route
        )
        spec_root, _, receipt_path = goals._goal_paths(project, identifier)
        spec_root.mkdir(parents=True)
        receipt_path.parent.mkdir(parents=True)
        for name, content in artifacts.items():
            (spec_root / name).write_bytes(content)
        relative_artifacts = {
            f".divan/specs/{identifier}/{name}": hashlib.sha256(
                content
            ).hexdigest()
            for name, content in artifacts.items()
        }
        receipt = receipts.new_receipt(
            identifier, intent, target, relative_artifacts
        )
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        route_before = (spec_root / "route.json").read_bytes()

        result = goals.start_goal(
            project,
            intent,
            target,
            True,
            host_profile="codex",
            context_window=context_window,
            environment={},
        )

        self.assertEqual(result["status"], "legacy-unchanged")
        self.assertTrue(result["migration_required"])
        self.assertEqual((spec_root / "route.json").read_bytes(), route_before)
        self.assertTrue(receipts.verify_receipt(receipt_path)["ok"])

    def test_human_plan_names_the_next_task_in_both_languages(self) -> None:
        project = self._project()
        for language, label in (("en", "Next"), ("tr", "Sıradaki")):
            with self.subTest(language=language):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "scripts/divan.py",
                        "plan",
                        "--project",
                        str(project),
                        "--intent",
                        "Build a small API feature",
                        "--host-profile",
                        "codex",
                        "--lang",
                        language,
                    ],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn(f"{label}: task-001", completed.stdout)


if __name__ == "__main__":
    unittest.main()
