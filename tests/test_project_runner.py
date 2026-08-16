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
    "agency_status.py",
    "cli.py",
    "cli_dispatch.py",
    "cli_parser.py",
    "ci_guard.py",
    "compatibility.py",
    "contract_validation.py",
    "desktop_api.py",
    "desktop_protocol.py",
    "desktop_protocol_support.py",
    "desktop_state.py",
    "engine.py",
    "engine_registry.py",
    "evidence.py",
    "executable_locator.py",
    "execution.py",
    "execution_contract.py",
    "execution_recovery.py",
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
    "spec_compiler.py",
    "spec_contract.py",
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
                self.assertIn("divan_runtime/adoption_runner.py", names)
                self.assertIn("divan_runtime/modules.json", names)
                self.assertIn("divan_runtime/messages.json", names)
                self.assertIn("divan_runtime/studio/index.html", names)
                self.assertIn("divan_runtime/studio/studio.css", names)
                self.assertIn("divan_runtime/studio/studio.js", names)
                self.assertEqual(
                    archive.read("divan_runtime/version.txt").decode("utf-8").strip(),
                    CURRENT_VERSION,
                )

    def test_dirty_tree_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            provider = (
                repository
                / "plugins"
                / "sadrazam"
                / "divan_runtime"
                / "providers.py"
            )
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

    def test_runner_executes_the_canonical_divan_runtime(self) -> None:
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
            payload = json.loads(execution.stdout)
            self.assertEqual(payload["status"], "valid")
            self.assertEqual(payload["product"]["id"], "divan")
            self.assertEqual(payload["module_count"], 9)

    def test_built_runner_serves_the_complete_seyir_session(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-pyz-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            repository.mkdir()
            source_commit = self._fixture(repository)
            output = base / "divan-project.pyz"
            result = self._build(repository, output, source_commit)
            self.assertEqual(result.returncode, 0, result.stderr)

            process = subprocess.Popen(
                [
                    sys.executable,
                    str(output),
                    "status",
                    "--project",
                    str(repository),
                    "--lang",
                    "tr",
                ],
                cwd=base,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            self.addCleanup(
                lambda: process.kill() if process.poll() is None else None
            )
            assert process.stdout is not None
            session_url = process.stdout.readline().strip()
            parsed = urllib.parse.urlsplit(session_url)
            self.assertEqual(parsed.hostname, "127.0.0.1")
            self.assertTrue(parsed.fragment)
            origin = f"http://127.0.0.1:{parsed.port}"

            for path in (
                "/session/",
                "/session/studio.css",
                "/session/studio.js",
            ):
                with urllib.request.urlopen(origin + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertTrue(response.read())
            request = urllib.request.Request(
                origin + "/api/status",
                headers={"X-Divan-Session": parsed.fragment},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.load(response)
            self.assertEqual(payload["product"]["name"], "Divan")
            self.assertEqual(payload["locale"], "tr")
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()
            assert process.stderr is not None
            process.stderr.close()

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