from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

import goals  # noqa: E402
import planning  # noqa: E402
import receipts  # noqa: E402


def sample_route() -> dict[str, object]:
    return {
        "schema_version": 2,
        "intent": "Fix the Python backend regression",
        "project": "sample",
        "workflow": "bugfix-delivery",
        "primary_workflow": "bugfix-delivery",
        "workflows": ["bugfix-delivery"],
        "providers": ["local"],
        "required_evidence": ["reproduction", "root cause", "regression test"],
        "frameworks": ["python"],
        "project_types": ["library"],
        "workspaces": [
            {
                "path": ".",
                "frameworks": ["python"],
                "project_types": ["library"],
                "package_managers": [],
            }
        ],
        "package_managers": [],
        "package_manager_conflicts": [],
        "commands": [
            {
                "workspace": ".",
                "manager": "python",
                "name": "test",
                "command": "python -m unittest discover",
            }
        ],
        "roles": ["backend-engineer", "qa-engineer", "independent-reviewer"],
        "stages": [
            "reproduce",
            "root cause",
            "regression test",
            "minimal fix",
            "verification",
        ],
        "packages": ["core-pack"],
        "skills": [
            {"package": "core-pack", "skill": "systematic-debugging"}
        ],
        "checks": ["python -m unittest discover"],
    }


class PlanningProfileTests(unittest.TestCase):
    def test_profiles_are_stable_and_include_portable_hosts(self) -> None:
        self.assertEqual(
            planning.profile_ids(COMPANY),
            ("chatgpt", "claude", "codex", "extended", "portable"),
        )

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown host planning profile"):
            planning.resolve_capacity("missing", directory=COMPANY)

    def test_fallback_capacity_never_claims_verified_model_limit(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                planning.PROFILE_ENV: "",
                planning.CONTEXT_ENV: "",
                "CLAUDE_PLUGIN_ROOT": "",
                "CLAUDE_CODE": "",
                "CODEX_HOME": "",
                "CODEX_THREAD_ID": "",
            },
            clear=False,
        ):
            result = planning.resolve_capacity("portable", directory=COMPANY)
        self.assertEqual(result["capacity_source"], "profile-fallback")
        self.assertEqual(result["capacity_kind"], "conservative-fallback")
        self.assertIn("not a verified model", result["warning"])


class SeferPlanningTests(unittest.TestCase):
    def test_small_route_can_fit_one_declared_session(self) -> None:
        result = planning.enrich_plan(
            sample_route(),
            host_profile="portable",
            context_window=128000,
            directory=COMPANY,
        )
        self.assertEqual(result["schema_version"], 3)
        self.assertEqual(result["recommended_sessions"], 1)
        self.assertEqual(result["orchestration_lane"], "tek-sefer")
        self.assertEqual(len(result["sefers"]), 1)
        self.assertEqual(result["context_budget"]["capacity_source"], "explicit-context-window")

    def test_large_compound_route_is_split_and_parallelism_is_bounded(self) -> None:
        route = sample_route()
        route.update(
            {
                "intent": "Baştan sona production release, security and documentation",
                "workflows": [
                    "security-delivery",
                    "testing-delivery",
                    "release-delivery",
                    "documentation-delivery",
                ],
                "roles": [
                    "product-strategist",
                    "backend-engineer",
                    "security-reviewer",
                    "technical-writer",
                    "release-manager",
                    "qa-engineer",
                    "independent-reviewer",
                ],
                "frameworks": ["nextjs", "react", "python"],
                "project_types": ["application", "monorepo", "public-web"],
                "workspaces": [
                    {"path": "."},
                    {"path": "apps/web"},
                    {"path": "services/api"},
                ],
                "stages": [
                    "threat model",
                    "test contract",
                    "red evidence",
                    "implementation",
                    "security review",
                    "public surface sync",
                    "CI",
                    "publication",
                    "live readback",
                ],
                "required_evidence": [
                    "threat model",
                    "red test evidence",
                    "green test evidence",
                    "CI result",
                    "release artifact",
                    "remote readback",
                ],
                "checks": [f"check-{index}" for index in range(12)],
            }
        )
        first = planning.enrich_plan(
            route,
            host_profile="extended",
            context_window=32000,
            target="released",
            directory=COMPANY,
        )
        second = planning.enrich_plan(
            route,
            host_profile="extended",
            context_window=32000,
            target="released",
            directory=COMPANY,
        )
        self.assertEqual(first, second)
        self.assertGreater(first["recommended_sessions"], 1)
        self.assertEqual(first["orchestration_lane"], "sinirli-ordu")
        self.assertLessEqual(first["safe_parallel_workstreams"], 3)
        self.assertTrue(
            first["publication_obligations"]["remote_readback_required"]
        )
        self.assertTrue(all(task["required_evidence"] for task in first["tasks"]))

    def test_goal_start_persists_machine_route_and_human_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='sample'\n", encoding="utf-8"
            )
            result = goals.start_goal(
                project,
                "Fix the Python backend regression",
                "verified",
                execute=True,
                host_profile="portable",
                context_window=128000,
            )
            goal_root = project / ".divan" / "specs" / result["goal_id"]
            route = json.loads(
                (goal_root / "route.json").read_text(encoding="utf-8")
            )
            plan = (goal_root / "plan.md").read_text(encoding="utf-8")
            tasks = (goal_root / "tasks.md").read_text(encoding="utf-8")
            receipt_path = project / result["receipt"]
            verification = receipts.verify_receipt(receipt_path)

        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(route["schema_version"], 3)
        self.assertIn("## Nizâm-ı Sefer", plan)
        self.assertIn("task-01", tasks)
        self.assertTrue(verification["ok"])
        self.assertIn("route.json", " ".join(verification["artifacts"]))


if __name__ == "__main__":
    unittest.main()
