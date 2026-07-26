from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_project_runner.py"
COMPANY = ROOT / "plugins" / "sadrazam" / "company"


def git(root: pathlib.Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *arguments],
        text=True,
        encoding="utf-8",
    ).strip()


class ProjectRunnerTests(unittest.TestCase):
    def _fixture(self, root: pathlib.Path) -> str:
        company = root / "plugins" / "sadrazam" / "company"
        company.mkdir(parents=True)
        for name in (
            "__init__.py",
            "adoption.py",
            "cli.py",
            "engine.py",
            "frameworks.json",
            "goal_archive.py",
            "goals.py",
            "impact-graph.json",
            "project_lifecycle.py",
            "project_os.py",
            "project_state.py",
            "project_transactions.py",
            "providers.py",
            "receipts.py",
            "roles.json",
            "workflows.json",
        ):
            shutil.copy2(COMPANY / name, company / name)
        (root / "VERSION").write_text("0.16.0\n", encoding="utf-8")
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
                source = json.loads(archive.read("divan-project-source.json"))
                self.assertEqual(
                    source,
                    {
                        "schema_version": 2,
                        "source_commit": source_commit,
                        "source_ref": "v0.16.0",
                        "source_repository": "https://github.com/trugurpala/divan",
                        "version": "0.16.0",
                    },
                )
                self.assertIn("project_state.py", names)

    def test_dirty_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            provider = repository / "plugins" / "sadrazam" / "company" / "providers.py"
            provider.write_text(provider.read_text(encoding="utf-8") + "\n# dirty\n")

            result = self._build(repository, base / "runner.pyz", source_commit)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("clean", result.stderr)

    def test_source_commit_must_equal_clean_head(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            self._fixture(repository)

            result = self._build(repository, base / "runner.pyz", "a" * 40)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("HEAD", result.stderr)

    def test_runner_executes_the_canonical_company_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "divan-project.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)

            execution = subprocess.run(
                [sys.executable, str(output), "validate", "--json"],
                cwd=temporary,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertEqual(json.loads(execution.stdout)["status"], "valid")

    def test_built_runner_initializes_and_audits_public_web_with_ci(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "divan-project.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)
            project = base / "site"
            state_path = pathlib.Path(tempfile.mkdtemp(
                prefix="divan-pyz-state-",
                dir=(
                    os.environ.get("LOCALAPPDATA")
                    if os.name == "nt"
                    else temporary
                ),
            ))
            if os.name == "nt":
                state_path.rmdir()
            self.addCleanup(
                lambda: shutil.rmtree(state_path)
                if state_path.exists()
                else None
            )
            environment = os.environ.copy()
            environment["DIVAN_STATE_HOME"] = str(state_path)
            shutil.copytree(
                ROOT / "tests" / "fixtures" / "projects" / "static-site",
                project,
            )
            init_args = [
                sys.executable,
                str(output),
                "init",
                "--project",
                str(project),
                "--profile",
                "standard",
                "--locale",
                "en",
                "--host",
                "agents",
                "--with-ci",
                "--expected-url",
                "https://example.test/",
                "--json",
            ]
            planned = subprocess.run(
                init_args,
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=False,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertNotIn("Traceback", planned.stderr)
            plan = json.loads(planned.stdout)
            self.assertEqual(plan["status"], "planned")
            paths = {row["path"] for row in plan["writes"]}
            self.assertIn(".github/workflows/divan-project.yml", paths)
            self.assertIn(".github/workflows/divan-seo.yml", paths)

            applied = subprocess.run(
                [*init_args, "--execute"],
                cwd=base,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=False,
            )
            self.assertEqual(
                applied.returncode, 0, applied.stderr + applied.stdout
            )
            self.assertEqual(json.loads(applied.stdout)["status"], "applied")
            expected_status = {
                "audit": {"PASS"},
                "verify": {"BLOCKED", "FAIL"},
            }
            for command in ("audit", "verify"):
                observed = subprocess.run(
                    [
                        sys.executable,
                        str(output),
                        command,
                        "--project",
                        str(project),
                        "--json",
                    ],
                    cwd=base,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=environment,
                    check=False,
                )
                self.assertNotIn("Traceback", observed.stderr)
                payload = json.loads(observed.stdout)
                self.assertIn(payload["status"], expected_status[command])
                self.assertLess(len(observed.stdout), 65536)


if __name__ == "__main__":
    unittest.main()
