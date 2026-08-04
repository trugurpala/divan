from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts" / "verify.py"


def load_verify():
    if not VERIFY_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("divan_verify", VERIFY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerificationRunnerTests(unittest.TestCase):
    def test_canonical_runner_exists(self) -> None:
        self.assertTrue(
            VERIFY_PATH.exists(),
            "scripts/verify.py must provide the shared local/CI verification path",
        )

    def test_core_sequence_starts_and_ends_with_hygiene(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)

        self.assertEqual(verify.CORE_COMMANDS[0], ("scripts/hygiene.py", "--check"))
        self.assertEqual(verify.CORE_COMMANDS[-1], ("scripts/hygiene.py", "--check"))
        self.assertIn(
            ("-m", "unittest", "discover", "-s", "tests", "-v"),
            verify.CORE_COMMANDS,
        )

    def test_coverage_mode_substitutes_one_instrumented_test_run(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)

        commands = verify.coverage_commands(verify.CORE_COMMANDS)

        self.assertNotIn(
            ("-m", "unittest", "discover", "-s", "tests", "-v"), commands
        )
        self.assertEqual(commands.count(verify.COVERAGE_TEST_COMMAND), 1)
        self.assertEqual(commands.count(verify.COVERAGE_REPORT_COMMAND), 1)
        self.assertEqual(verify.command_class(verify.COVERAGE_TEST_COMMAND), "test")

    def test_environment_keeps_generated_caches_outside_repository(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as cache:
            environment = verify.verification_environment(
                pathlib.Path(repo), pathlib.Path(cache)
            )

            self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
            for name in (
                "PYTHONPYCACHEPREFIX",
                "RUFF_CACHE_DIR",
                "MYPY_CACHE_DIR",
                "COVERAGE_FILE",
            ):
                path = pathlib.Path(environment[name]).resolve()
                self.assertTrue(path.is_relative_to(pathlib.Path(cache).resolve()))
                self.assertFalse(path.is_relative_to(pathlib.Path(repo).resolve()))

    def test_every_child_and_the_overall_verify_have_finite_timeouts(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)
        completed = mock.Mock(returncode=0)
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as cache:
            with (
                mock.patch.object(verify.subprocess, "run", return_value=completed) as run,
                mock.patch.object(
                    verify.timeouts,
                    "resolve_default",
                    side_effect=lambda name: mock.Mock(
                        command_class=name,
                        configured_seconds=300 if name == "verify" else 120,
                    ),
                ) as resolve,
            ):
                result = verify.run(
                    root=pathlib.Path(repo),
                    commands=(("scripts/probe.py",),),
                    cache_root=pathlib.Path(cache),
                )

        self.assertEqual(result, 0)
        self.assertEqual(
            [call.args[0] for call in resolve.call_args_list],
            ["verify", "fast-check"],
        )
        self.assertGreater(run.call_args.kwargs["timeout"], 0)
        self.assertLessEqual(run.call_args.kwargs["timeout"], 120)

    def test_overall_budget_never_shortens_the_largest_child_budget(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)
        completed = mock.Mock(returncode=0)
        decisions = {
            "verify": mock.Mock(command_class="verify", configured_seconds=300),
            "test": mock.Mock(command_class="test", configured_seconds=600),
        }
        command = ("-m", "unittest", "discover", "-s", "tests", "-v")
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as cache:
            with (
                mock.patch.object(verify.subprocess, "run", return_value=completed) as run,
                mock.patch.object(
                    verify.timeouts,
                    "resolve_default",
                    side_effect=lambda name: decisions[name],
                ),
            ):
                result = verify.run(
                    root=pathlib.Path(repo),
                    commands=(command,),
                    cache_root=pathlib.Path(cache),
                )

        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.kwargs["timeout"], 600)

    def test_child_python_uses_current_interpreter_and_preserves_user_files(self) -> None:
        verify = load_verify()
        self.assertIsNotNone(verify)
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as cache:
            root = pathlib.Path(repo)
            scripts = root / "scripts"
            scripts.mkdir()
            (root / "protected.txt").write_text("keep", encoding="utf-8")
            (scripts / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            (scripts / "probe.py").write_text(
                "import module\n"
                "import os\n"
                "import pathlib\n"
                "pathlib.Path('interpreter.txt').write_text("
                "os.path.realpath(os.sys.executable), encoding='utf-8')\n",
                encoding="utf-8",
            )

            result = verify.run(
                root=root,
                commands=(("scripts/probe.py",),),
                cache_root=pathlib.Path(cache),
            )

            self.assertEqual(result, 0)
            self.assertEqual((root / "protected.txt").read_text(encoding="utf-8"), "keep")
            self.assertEqual(
                os.path.realpath((root / "interpreter.txt").read_text(encoding="utf-8")),
                os.path.realpath(sys.executable),
            )
            self.assertEqual(list(root.rglob("__pycache__")), [])

    def test_documentation_ci_and_release_manifest_share_the_runner(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "quality-gate.yml").read_text(
            encoding="utf-8"
        )
        manifest = (ROOT / "release-manifest.json").read_text(encoding="utf-8")

        self.assertIn("python scripts/verify.py", agents)
        self.assertIn("python scripts/verify.py", workflow)
        self.assertIn('"path": "scripts/verify.py"', manifest)

    def test_agents_contract_requires_evidence_first_benchmarking(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for requirement in (
            "Baseline'ı en az üç bağımsız ölçümle çalıştır",
            "en az üç anlamlı",
            "her adayı da en az üç kez ölç",
            "tam commit SHA'sı",
            "ölçüm gürültüsünden büyükse",
            "kullanıcının başlangıç değişikliklerine dokunma",
            "Windows 11 + PowerShell + Codex",
            "Timeout",
        ):
            self.assertIn(requirement, agents)


if __name__ == "__main__":
    unittest.main()
