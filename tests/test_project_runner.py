from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_project_runner.py"
RUNTIME = ROOT / "plugins" / "sadrazam" / "divan_runtime"
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RUNTIME_FILES = (
    "__init__.py",
    "adoption.py",
    "adoption_common.py",
    "adoption_legacy.py",
    "adoption_proof.py",
    "adoption_proof_common.py",
    "adoption_proof_execution.py",
    "adoption_runner.py",
    "adoption_schema2.py",
    "cli.py",
    "cli_dispatch.py",
    "cli_parser.py",
    "ci_guard.py",
    "compatibility.py",
    "contract_validation.py",
    "desktop_api.py",
    "desktop_protocol.py",
    "desktop_state.py",
    "engine.py",
    "engine_registry.py",
    "evidence.py",
    "executable_locator.py",
    "execution.py",
    "execution_contract.py",
    "execution_router.py",
    "frameworks.json",
    "git_guard.py",
    "goal_archive.py",
    "goals.py",
    "governance.json",
    "governance.py",
    "impact-graph.json",
    "kernel.py",
    "local_server.py",
    "locales.py",
    "messages.json",
    "modules.json",
    "native_engine.py",
    "orca_adapter.py",
    "orca_engine.py",
    "orchestrator.py",
    "planning.py",
    "planning_policy.py",
    "project_lifecycle.py",
    "project_os.py",
    "project_readiness.py",
    "project_registry.py",
    "project_state.py",
    "project_transactions.py",
    "providers.py",
    "receipts.py",
    "release.py",
    "review_gate.py",
    "reviewer_runner.py",
    "roles.json",
    "runtime_composition.py",
    "seyir_state.py",
    "status.py",
    "task_model.py",
    "task_store.py",
    "timeouts.py",
    "data/timeout-benchmarks.json",
    "data/timeout-policy.json",
    "studio/index.html",
    "studio/studio.css",
    "studio/studio.js",
    "version.txt",
    "workflows.json",
)


def git(root: pathlib.Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *arguments],
        text=True,
        encoding="utf-8",
    ).strip()


class ProjectRunnerTests(unittest.TestCase):
    def _fixture(self, root: pathlib.Path) -> str:
        runtime = root / "plugins" / "sadrazam" / "divan_runtime"
        runtime.mkdir(parents=True)
        for name in RUNTIME_FILES:
            (runtime / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RUNTIME / name, runtime / name)
        (root / "VERSION").write_text(CURRENT_VERSION + "\n", encoding="utf-8")
        registry = root / "registry"
        registry.mkdir()
        shutil.copy2(ROOT / "registry" / "seo-policy.json", registry)
        subprocess.run(["git", "-C", str(root), "init", "--quiet"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "core.autocrlf", "false"],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=Divan Test",
                "-c",
                "user.email=divan-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            check=True,
        )
        return git(root, "rev-parse", "HEAD")

    def _build(
        self, root: pathlib.Path, output: pathlib.Path, source_commit: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--root",
                str(root),
                "--output",
                str(output),
                "--source-commit",
                source_commit,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_two_verified_tree_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            first = base / "first.pyz"
            second = base / "second.pyz"

            for output in (first, second):
                result = self._build(repository, output, source_commit)
                self.assertEqual(result.returncode, 0, result.stderr)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertTrue(
                    all(
                        item.date_time == (1980, 1, 1, 0, 0, 0)
                        for item in archive.infolist()
                    )
                )
                source = json.loads(
                    archive.read("divan_runtime/divan-project-source.json")
                )
                self.assertEqual(
                    source,
                    {
                        "schema_version": 2,
                        "source_commit": source_commit,
                        "source_ref": f"v{CURRENT_VERSION}",
                        "source_repository": "https://github.com/trugurpala/divan",
                        "version": CURRENT_VERSION,
                    },
                )
                self.assertIn("divan_runtime/project_state.py", names)
                self.assertIn("divan_runtime/executable_locator.py", names)
                self.assertIn("divan_runtime/project_readiness.py", names)
                self.assertIn("divan_runtime/desktop_protocol.py", names)
                self.assertIn("divan_runtime/timeout-policy.json", names)

    def test_source_commit_must_equal_clean_head(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            self._fixture(repository)
            output = base / "runner.pyz"
            result = self._build(repository, output, "0" * 40)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly match clean repository HEAD", result.stderr)
            self.assertFalse(output.exists())

    def test_dirty_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            (repository / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            output = base / "runner.pyz"
            result = self._build(repository, output, source_commit)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source repository must be clean", result.stderr)
            self.assertFalse(output.exists())

    def test_runner_executes_the_canonical_divan_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "runner.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)

            completed = subprocess.run(
                [sys.executable, str(output), "validate", "--json"],
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "valid")
            self.assertEqual(payload["module_count"], 9)

    def test_built_runner_serves_the_complete_seyir_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "runner.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)

            project = base / "project"
            project.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(output),
                    "project",
                    "status",
                    str(project),
                    "--json",
                ],
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIn("project", payload)

    def test_built_runner_initializes_and_audits_public_web_with_ci(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "runner.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)

            project = base / "project"
            project.mkdir()
            (project / "package.json").write_text(
                json.dumps({"scripts": {"build": "echo ok"}}), encoding="utf-8"
            )
            subprocess.run(["git", "-C", str(project), "init", "--quiet"], check=True)
            subprocess.run(
                ["git", "-C", str(project), "config", "core.autocrlf", "false"],
                check=True,
            )
            subprocess.run(["git", "-C", str(project), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(project),
                    "-c",
                    "user.name=Divan Test",
                    "-c",
                    "user.email=divan-test@example.invalid",
                    "commit",
                    "--quiet",
                    "-m",
                    "fixture",
                ],
                check=True,
            )

            init = subprocess.run(
                [
                    sys.executable,
                    str(output),
                    "project",
                    "init",
                    str(project),
                    "--profile",
                    "public-web",
                    "--ci",
                    "--execute",
                    "--json",
                ],
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            audit = subprocess.run(
                [
                    sys.executable,
                    str(output),
                    "project",
                    "audit",
                    str(project),
                    "--json",
                ],
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            payload = json.loads(audit.stdout)
            self.assertIn(payload["status"], {"ready", "needs-attention"})


if __name__ == "__main__":
    unittest.main()
