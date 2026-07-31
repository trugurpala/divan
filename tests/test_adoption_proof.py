from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import execution, goals, project_os, receipts  # noqa: E402

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

    @staticmethod
    def runner_digest(path: pathlib.Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    def create_verified_project(
        self,
        root: pathlib.Path,
        scripts: dict[str, str] | None = None,
        *,
        source: dict[str, str] = SOURCE,
        bind_verification_evidence: bool = True,
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
        verification = (
            root / ".divan" / "evidence" / result["goal_id"] / "verification.md"
        )
        verification.write_text("native checks passed\n", encoding="utf-8")
        relative_verification = verification.relative_to(root).as_posix()
        verification_digest = hashlib.sha256(verification.read_bytes()).hexdigest()
        for state in ("SPECIFIED", "PLANNED", "IMPLEMENTING", "VERIFIED"):
            final = state == "VERIFIED" and bind_verification_evidence
            receipts.append_transition(
                receipt_path,
                state,
                evidence=[relative_verification] if final else None,
                bind_artifacts=(
                    {relative_verification: verification_digest}
                    if final
                    else None
                ),
            )
        runner = root.parent / "divan-project.pyz"
        with zipfile.ZipFile(runner, "w") as archive:
            archive.writestr(
                "divan_runtime/divan-project-source.json",
                json.dumps({"schema_version": 2, **source}, sort_keys=True)
                + "\n",
            )
        digest = hashlib.sha256(runner.read_bytes()).hexdigest()
        runner.with_name(runner.name + ".sha256").write_text(
            f"{digest}  {runner.name}\n", encoding="utf-8"
        )
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
                expected_runner_sha256=self.runner_digest(runner),
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

    def test_preview_rejects_verified_goal_without_execution_evidence(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-goal-evidence-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            goal_id, runner = self.create_verified_project(
                root, bind_verification_evidence=False
            )

            with self.assertRaisesRegex(ValueError, "verification evidence"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "claude-code",
                    runner_path=runner,
                    expected_runner_sha256=self.runner_digest(runner),
                )

    def test_goal_bound_check_survives_the_eight_check_cap(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-priority-"
        ) as temporary:
            root = pathlib.Path(temporary)
            commands = [
                {
                    "workspace": ".",
                    "manager": "bun",
                    "name": f"test:{letter}",
                    "command": f"bun run test:{letter}",
                }
                for letter in "abcdefghi"
            ]
            inspection = {
                "package_manager_conflicts": [],
                "commands": commands,
            }
            selected = module.select_checks(
                inspection, {"checks": ["bun run test:i"]}, root
            )

            self.assertEqual(len(selected), 8)
            self.assertIn("test:i", {row["name"] for row in selected})
            with self.assertRaisesRegex(ValueError, "more than eight"):
                module.select_checks(
                    inspection,
                    {"checks": [row["command"] for row in commands]},
                    root,
                )
            with self.assertRaisesRegex(
                ValueError, "unavailable or unsupported"
            ):
                module.select_checks(
                    inspection,
                    {"checks": ["bun run test:missing"]},
                    root,
                )

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

    def test_release_authority_requires_exact_tag_asset_url_and_digest(
        self,
    ) -> None:
        module = self.require_module()
        payload = {
            "tag_name": SOURCE["source_ref"],
            "draft": False,
            "assets": [
                {
                    "name": "divan-project.pyz",
                    "browser_download_url": (
                        "https://github.com/trugurpala/divan/releases/download/"
                        f"{SOURCE['source_ref']}/divan-project.pyz"
                    ),
                    "digest": "sha256:" + "c" * 64,
                }
            ],
        }

        self.assertEqual(
            module.adoption_runner._release_asset_digest(payload, SOURCE),
            "sha256:" + "c" * 64,
        )
        for key, value in (
            ("tag_name", "v9.9.9"),
            ("draft", True),
            ("assets", []),
        ):
            with self.subTest(key=key):
                forged = {**payload, key: value}
                with self.assertRaisesRegex(ValueError, "authority"):
                    module.adoption_runner._release_asset_digest(
                        forged, SOURCE
                    )

    def test_distinct_project_policy_allows_common_version_and_other_marketplace(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-distinct-"
        ) as temporary:
            root = pathlib.Path(temporary)
            self.assertTrue(module.classify_distinct_project(root)["distinct"])

            (root / "VERSION").write_text("0.18.3\n", encoding="utf-8")
            marketplace = root / ".claude-plugin" / "marketplace.json"
            marketplace.parent.mkdir()
            marketplace.write_text('{"name":"another-product"}\n', encoding="utf-8")
            self.assertTrue(module.classify_distinct_project(root)["distinct"])

    def test_distinct_project_policy_blocks_strong_divan_signatures(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-distinct-"
        ) as temporary:
            root = pathlib.Path(temporary)
            marketplace = root / ".claude-plugin" / "marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text('{"name":"divan"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "partial Divan signature"):
                module.classify_distinct_project(root)

            (root / "VERSION").write_text("0.18.3\n", encoding="utf-8")
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

    def test_preflight_rejects_missing_checksum_and_forged_runner_identity(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-runner-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            goal_id, runner = self.create_verified_project(root)
            original_digest = self.runner_digest(runner)
            checksum = runner.with_name(runner.name + ".sha256")
            checksum.unlink()
            with self.assertRaisesRegex(ValueError, "checksum"):
                module.build_proof_plan(
                    root, goal_id, "codex", runner_path=runner
                )

            forged_source = {**SOURCE, "source_commit": "b" * 40}
            with zipfile.ZipFile(runner, "w") as archive:
                archive.writestr(
                    "divan_runtime/divan-project-source.json",
                    json.dumps(
                        {"schema_version": 2, **forged_source}, sort_keys=True
                    )
                    + "\n",
                )
            digest = hashlib.sha256(runner.read_bytes()).hexdigest()
            checksum.write_text(
                f"{digest}  {runner.name}\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "release authority"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "codex",
                    runner_path=runner,
                    expected_runner_sha256=original_digest,
                )
            with self.assertRaisesRegex(ValueError, "source identity"):
                module.build_proof_plan(
                    root,
                    goal_id,
                    "codex",
                    runner_path=runner,
                    expected_runner_sha256=self.runner_digest(runner),
                )


class CleanRoomProofExecutionTests(CleanRoomProofPlanningTests):
    def make_plan(
        self, root: pathlib.Path, host: str = "claude-code"
    ) -> dict[str, object]:
        module = self.require_module()
        goal_id, runner = self.create_verified_project(root)
        return module.build_proof_plan(
            root,
            goal_id,
            host,
            "maintainer",
            runner_path=runner,
            expected_runner_sha256=self.runner_digest(runner),
        )

    @staticmethod
    def result(
        status: str = "PASS",
        returncode: int | None = 0,
        stdout: str = "",
        stderr: str = "",
        elapsed: float = 0.01,
    ) -> execution.ExecutionResult:
        return execution.ExecutionResult(
            status=status,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            elapsed_seconds=elapsed,
            timeout={},
            mutating=False,
            retry_allowed=False,
            next_action="",
        )

    def test_windows_host_probe_prefers_runnable_command_shim(self) -> None:
        module = self.require_module()
        seen: list[str] = []

        def fake_which(command: str) -> str | None:
            seen.append(command)
            if command == "codex.cmd":
                return r"C:\tools\codex.cmd"
            if command == "codex":
                return r"C:\tools\codex"
            return None

        resolved = (
            module.adoption_proof_common.resolved_host_probe_command(
                "codex", platform="nt", which=fake_which
            )
        )

        self.assertEqual(resolved, (r"C:\tools\codex.cmd", "--version"))
        self.assertEqual(seen, ["codex.cmd"])

    def test_non_windows_host_probe_preserves_portable_command(self) -> None:
        module = self.require_module()

        resolved = (
            module.adoption_proof_common.resolved_host_probe_command(
                "claude-code",
                platform="posix",
                which=lambda _command: "/ignored",
            )
        )

        self.assertEqual(resolved, ("claude", "--version"))

    def test_success_journals_pending_before_checks_and_promotes_receipts(
        self,
    ) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-execute-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            calls: list[tuple[str, ...]] = []
            pending_seen: list[bool] = []

            def fake_runner(command, _decision, **kwargs):
                argv = tuple(command)
                calls.append(argv)
                if kwargs.get("mutating"):
                    journal = (
                        root
                        / ".divan"
                        / "adoption"
                        / ".staging"
                        / plan["proof_id"]
                        / "journal.json"
                    )
                    payload = json.loads(journal.read_text(encoding="utf-8"))
                    pending_seen.append(
                        payload["checks"][-1]["status"] == "pending"
                    )
                    return self.result(
                        stdout="55 tests passed\n",
                        elapsed=0.2,
                    )
                return self.result(stdout="Claude Code 2.1.220\n")

            moments = iter(
                (
                    datetime(2026, 7, 30, 10, 0, tzinfo=timezone.utc),
                    datetime(2026, 7, 30, 10, 1, tzinfo=timezone.utc),
                )
            )
            result = module.execute_proof(
                plan,
                command_runner=fake_runner,
                clock=lambda: next(moments),
            )

            final = (
                root / ".divan" / "adoption" / str(plan["proof_id"])
            )
            self.assertEqual(result["status"], "passed")
            self.assertEqual(
                result["receipt_status"], "valid-clean-room-adoption"
            )
            self.assertTrue(pending_seen)
            self.assertEqual(calls[0], ("claude", "--version"))
            self.assertTrue((final / "adoption-receipt.json").is_file())
            self.assertTrue((final / "adoption-receipt.md").is_file())
            self.assertTrue((final / "journal.json").is_file())
            self.assertFalse(
                (
                    root
                    / ".divan"
                    / "adoption"
                    / ".staging"
                    / str(plan["proof_id"])
                ).exists()
            )
            json_text = (final / "adoption-receipt.json").read_text(
                encoding="utf-8"
            )
            self.assertNotIn(str(root), json_text)
            self.assertNotIn("vitest run", json_text)
            self.assertEqual(
                module.adoption.verify_adoption(
                    final / "adoption-receipt.json"
                )["status"],
                "valid-clean-room-adoption",
            )
            self.assertEqual(
                module.adoption.verify_adoption(
                    final / "adoption-receipt.md"
                )["status"],
                "valid-clean-room-adoption",
            )

    def test_failure_timeout_and_cancel_stop_without_promotion(self) -> None:
        module = self.require_module()
        cases = (
            ("FAILED", 2, "failed-checks"),
            ("TIMEOUT", None, "failed-checks"),
            ("CANCELLED", None, "cancelled"),
        )
        for command_status, returncode, expected in cases:
            with self.subTest(command_status=command_status):
                with tempfile.TemporaryDirectory(
                    prefix="divan-proof-failure-"
                ) as temporary:
                    root = pathlib.Path(temporary) / "project"
                    root.mkdir()
                    plan = self.make_plan(root)
                    project_calls = 0

                    def fake_runner(command, _decision, **kwargs):
                        nonlocal project_calls
                        if not kwargs.get("mutating"):
                            return self.result(
                                stdout="Claude Code 2.1.220\n"
                            )
                        project_calls += 1
                        return self.result(
                            command_status,
                            returncode,
                            stderr="bounded failure",
                        )

                    result = module.execute_proof(
                        plan, command_runner=fake_runner
                    )
                    staging = (
                        root
                        / ".divan"
                        / "adoption"
                        / ".staging"
                        / str(plan["proof_id"])
                    )
                    final = (
                        root
                        / ".divan"
                        / "adoption"
                        / str(plan["proof_id"])
                    )
                    self.assertEqual(result["status"], expected)
                    self.assertEqual(project_calls, 1)
                    self.assertTrue((staging / "journal.json").is_file())
                    self.assertFalse(final.exists())
                    self.assertFalse(
                        (staging / "adoption-receipt.json").exists()
                    )

    def test_project_identity_drift_blocks_receipt(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-drift-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            changed = False

            def fake_runner(command, _decision, **kwargs):
                nonlocal changed
                if not kwargs.get("mutating"):
                    return self.result(stdout="Claude Code 2.1.220\n")
                if not changed:
                    changed = True
                    package = root / "package.json"
                    package.write_text(
                        package.read_text(encoding="utf-8") + "\n",
                        encoding="utf-8",
                    )
                return self.result(stdout="passed\n")

            result = module.execute_proof(
                plan, command_runner=fake_runner
            )

            self.assertEqual(result["status"], "invalid")
            self.assertIn("changed", result["reason"])
            self.assertFalse(
                (
                    root
                    / ".divan"
                    / "adoption"
                    / str(plan["proof_id"])
                ).exists()
            )

    def test_git_tracked_source_drift_blocks_receipt(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-git-drift-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            changed = False

            def fake_runner(command, _decision, **kwargs):
                nonlocal changed
                argv = tuple(command)
                if argv[0] == "git":
                    return self.result(
                        stdout="after\n" if changed else "before\n"
                    )
                if not kwargs.get("mutating"):
                    return self.result(stdout="Claude Code 2.1.220\n")
                changed = True
                return self.result(stdout="passed\n")

            result = module.execute_proof(
                plan, command_runner=fake_runner
            )

            self.assertEqual(result["status"], "invalid")
            self.assertIn("tracked source", result["reason"])

    def test_git_head_change_blocks_a_commit_during_checks(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-git-head-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            changed = False

            def fake_runner(command, _decision, **kwargs):
                nonlocal changed
                argv = tuple(command)
                if argv[:3] == ("git", "rev-parse", "--verify"):
                    return self.result(stdout=("b" if changed else "a") * 40)
                if argv[0] == "git":
                    return self.result(stdout="")
                if not kwargs.get("mutating"):
                    return self.result(stdout="Claude Code 2.1.220\n")
                changed = True
                return self.result(stdout="passed\n")

            result = module.execute_proof(
                plan, command_runner=fake_runner
            )

            self.assertEqual(result["status"], "invalid")
            self.assertIn("tracked source", result["reason"])

    def test_execution_uses_fresh_private_commands_after_preview(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-fresh-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            plan["_private"]["checks"][0]["argv"] = (
                "powershell",
                "-Command",
                "Write-Output substituted",
            )
            executed: list[tuple[str, ...]] = []

            def fake_runner(command, _decision, **kwargs):
                argv = tuple(command)
                if argv[0] == "git":
                    return self.result(stdout="")
                if not kwargs.get("mutating"):
                    return self.result(stdout="Claude Code 2.1.220\n")
                executed.append(argv)
                return self.result(stdout="passed\n")

            result = module.execute_proof(
                plan, command_runner=fake_runner
            )

            self.assertEqual(result["status"], "passed")
            self.assertNotIn("powershell", executed[0])
            self.assertIn(("bun", "run", "test"), executed)

    def test_existing_final_proof_is_never_overwritten(self) -> None:
        module = self.require_module()
        with tempfile.TemporaryDirectory(
            prefix="divan-proof-existing-"
        ) as temporary:
            root = pathlib.Path(temporary) / "project"
            root.mkdir()
            plan = self.make_plan(root)
            final = (
                root / ".divan" / "adoption" / str(plan["proof_id"])
            )
            final.mkdir(parents=True)
            marker = final / "marker.txt"
            marker.write_text("keep\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "already exists"):
                module.execute_proof(
                    plan,
                    command_runner=lambda *_args, **_kwargs: self.fail(
                        "no process should start"
                    ),
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
