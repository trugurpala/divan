from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import goals, project_os, receipts  # noqa: E402

try:
    from divan_runtime import adoption_proof  # noqa: E402
except ImportError:
    adoption_proof = None

SOURCE = {
    "version": "0.18.3",
    "source_repository": "https://github.com/trugurpala/divan",
    "source_ref": "v0.18.3",
    "source_commit": "a" * 40,
}


class CleanRoomProofPlanningTests(unittest.TestCase):
    def require_module(self):
        if adoption_proof is None:
            self.fail("adoption_proof module is not implemented")
        return adoption_proof

    def create_verified_project(
        self,
        root: pathlib.Path,
        scripts: dict[str, str] | None = None,
        *,
        source: dict[str, str] = SOURCE,
    ) -> tuple[str, pathlib.Path]:
        package = {
            "name": "external-sample",
            "version": "1.0.0",
            "private": True,
            "packageManager": "bun@1.2.0",
            "scripts": scripts
            or {
                "test": "vitest run",
                "typecheck": "tsc --noEmit",
                "lint": "eslint .",
                "build": "vite build",
            },
        }
        (root / "package.json").write_text(
            json.dumps(package) + "\n", encoding="utf-8"
        )
        with mock.patch.object(
            project_os, "_runtime_source_identity", return_value=source
        ):
            project_os.apply_init_plan(
                project_os.build_init_plan(
                    root, "standard", "en", ("agents",), False
                )
            )
        result = goals.start_goal(
            root, "Verify a real project", "verified", execute=True
        )
        receipt_path = root / result["receipt"]
        for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
            receipts.append_transition(receipt_path, state)
        runner = root.parent / "divan-project.pyz"
        runner.write_bytes(b"released-divan-project-runner")
        return result["goal_id"], runner

    def test_preview_plan_is_bounded_test_backed_and_write_free(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-plan-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            goal_id, runner = self.create_verified_project(root)

            plan = module.build_proof_plan(
                root,
                goal_id,
                "claude-code",
                "maintainer",
                runner_path=runner,
            )

            self.assertEqual(plan["status"], "ready")
            self.assertEqual(plan["schema_version"], 1)
            self.assertEqual(plan["host_probe"]["argv"], ("claude", "--version"))
            self.assertEqual(plan["host_probe"]["status"], "planned")
            self.assertGreaterEqual(len(plan["checks"]), 1)
            self.assertLessEqual(len(plan["checks"]), 8)
            self.assertTrue(
                any(row["class"] == "test" for row in plan["checks"])
            )
            self.assertEqual(
                [row["id"] for row in plan["checks"]],
                sorted(row["id"] for row in plan["checks"]),
            )
            self.assertFalse((root / ".divan" / "adoption").exists())

    def test_safe_argv_supports_only_bounded_native_runners(self) -> None:
        module = self.require_module()
        cases = (
            ({"manager": "npm", "name": "test"}, ("npm", "run", "test")),
            (
                {"manager": "pnpm", "name": "typecheck"},
                ("pnpm", "run", "typecheck"),
            ),
            ({"manager": "bun", "name": "lint"}, ("bun", "run", "lint")),
            (
                {"manager": "python", "name": "test"},
                (sys.executable, "-m", "unittest", "discover"),
            ),
            ({"manager": "go", "name": "test"}, ("go", "test", "./...")),
            ({"manager": "cargo", "name": "test"}, ("cargo", "test")),
        )
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(module.safe_argv(command), expected)

        unsafe = (
            {"manager": "bun", "name": "test && curl example.invalid"},
            {"manager": "../bun", "name": "test"},
            {"manager": "powershell", "name": "test"},
            {"manager": "npm", "name": "A=1"},
        )
        for command in unsafe:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    module.safe_argv(command)

    def test_distinct_project_policy_blocks_complete_and_partial_divan_signatures(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-distinct-"
        ) as temporary:
            root = pathlib.Path(temporary)
            self.assertTrue(module.classify_distinct_project(root)["distinct"])

            (root / "VERSION").write_text("0.18.3\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "partial Divan signature"):
                module.classify_distinct_project(root)

            marketplace = root / ".claude-plugin" / "marketplace.json"
            marketplace.parent.mkdir()
            marketplace.write_text('{"name":"divan"}\n', encoding="utf-8")
            runtime_modules = (
                root
                / "plugins"
                / "sadrazam"
                / "divan_runtime"
                / "modules.json"
            )
            runtime_modules.parent.mkdir(parents=True)
            runtime_modules.write_text('{"schema_version":1}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Divan source tree"):
                module.classify_distinct_project(root)

    def test_preflight_rejects_mutable_source_unsupported_host_and_build_only(
        self,
    ) -> None:
        module = self.require_module()
        mutable = {
            **SOURCE,
            "source_ref": "development@" + "b" * 40,
            "source_commit": "b" * 40,
        }
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-reject-"
        ) as temporary:
            root = pathlib.Path(temporary) / "mutable"
            root.mkdir()
            goal_id, runner = self.create_verified_project(
                root, source=mutable
            )
            with self.assertRaisesRegex(ValueError, "immutable release"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "claude-code",
                    runner_path=runner,
                )

        with tempfile.TemporaryDirectory(
            prefix="divan-proof-reject-"
        ) as temporary:
            root = pathlib.Path(temporary) / "host"
            root.mkdir()
            goal_id, runner = self.create_verified_project(root)
            with self.assertRaisesRegex(ValueError, "host"):
                module.build_proof_plan(
                    root, goal_id, "cursor", runner_path=runner
                )

        with tempfile.TemporaryDirectory(
            prefix="divan-proof-reject-"
        ) as temporary:
            root = pathlib.Path(temporary) / "build-only"
            root.mkdir()
            goal_id, runner = self.create_verified_project(
                root, {"build": "vite build"}
            )
            with self.assertRaisesRegex(ValueError, "test-class"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "codex",
                    runner_path=runner,
                )

    def test_preflight_rejects_tampered_goal_and_unsafe_operator(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-reject-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            goal_id, runner = self.create_verified_project(root)
            receipt_path = (
                root / ".divan" / "evidence" / goal_id / "receipt.json"
            )
            payload = json.loads(receipt_path.read_text(encoding="utf-8"))
            payload["state"] = "IMPLEMENTING"
            receipt_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "goal receipt"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "codex",
                    runner_path=runner,
                )
            with self.assertRaisesRegex(ValueError, "operator"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "codex",
                    "independent",
                    runner_path=runner,
                )


if __name__ == "__main__":
    unittest.main()
