from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_bootstrap.py"


def load_builder():
    if not BUILDER.is_file():
        raise AssertionError("scripts/build_bootstrap.py is missing")
    spec = importlib.util.spec_from_file_location("divan_bootstrap_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BootstrapRunnerTests(unittest.TestCase):
    def _fixture(self, destination: pathlib.Path) -> str:
        shutil.copytree(
            ROOT,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                ".worktrees",
                "__pycache__",
                "*.pyc",
                ".coverage",
            ),
        )
        subprocess.run(["git", "init", "--quiet"], cwd=destination, check=True)
        subprocess.run(
            ["git", "config", "core.autocrlf", "false"],
            cwd=destination,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=destination, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Divan Test",
                "-c",
                "user.email=divan-test@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            cwd=destination,
            check=True,
        )
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=destination,
            text=True,
            encoding="utf-8",
        ).strip()

    def _build(
        self,
        repository: pathlib.Path,
        output: pathlib.Path,
        source_commit: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(repository / "scripts" / "build_bootstrap.py"),
                "--root",
                str(repository),
                "--output",
                str(output),
                "--source-commit",
                source_commit,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_two_clean_builds_are_identical_and_bounded(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory(prefix="divan-bootstrap-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
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
                self.assertEqual(set(names), set(builder.archive_names(repository)))
                self.assertTrue(
                    all(
                        item.date_time == (1980, 1, 1, 0, 0, 0)
                        for item in archive.infolist()
                    )
                )
                identity = json.loads(
                    archive.read("divan-bootstrap-source.json")
                )
                self.assertEqual(identity["source_commit"], source_commit)
                self.assertEqual(
                    identity["source_ref"],
                    f"v{(repository / 'VERSION').read_text().strip()}",
                )
                self.assertIn("scripts/divan.py", names)
                self.assertIn("scripts/host_install_marketplace.py", names)
                self.assertIn("scripts/host_install_recovery.py", names)
                self.assertIn(
                    "plugins/sadrazam/divan_runtime/studio/index.html",
                    names,
                )
                uiux_license = (
                    "plugins/ui-pack/skills/ui-ux-pro-max/LICENSE.txt"
                )
                self.assertIn(uiux_license, names)
                self.assertEqual(
                    archive.read(uiux_license),
                    (
                        repository
                        / "plugins"
                        / "ui-pack"
                        / "LICENSE-uiuxpromax-MIT.txt"
                    ).read_bytes(),
                )
                skill_manifests = [
                    name
                    for name in names
                    if name.startswith("plugins/")
                    and "/skills/" in name
                    and name.endswith("/SKILL.md")
                ]
                self.assertEqual(len(skill_manifests), 42)

    def test_bootstrap_runs_doctor_without_checkout_or_ref(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-bootstrap-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            source_commit = self._fixture(repository)
            output = base / "divan.pyz"
            built = self._build(repository, output, source_commit)
            self.assertEqual(built.returncode, 0, built.stderr)
            empty = base / "empty"
            empty.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(output),
                    "doctor",
                    "--host",
                    "codex",
                    "--json",
                ],
                cwd=empty,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["ref"], f"v{(repository / 'VERSION').read_text().strip()}")
            self.assertIn("codex", payload["hosts"])
            self.assertIn(payload["status"], {"healthy", "attention", "unavailable"})
            self.assertIsInstance(payload["next_command"], str)
            if payload["status"] == "healthy":
                self.assertEqual(payload["next_command"], "")
            else:
                self.assertTrue(payload["next_command"])

    def test_bootstrap_rejects_a_ref_other_than_its_bundled_release(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-bootstrap-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            source_commit = self._fixture(repository)
            output = base / "divan.pyz"
            built = self._build(repository, output, source_commit)
            self.assertEqual(built.returncode, 0, built.stderr)

            result = subprocess.run(
                [
                    sys.executable,
                    str(output),
                    "doctor",
                    "--host",
                    "codex",
                    "--ref",
                    "v0.0.0",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=10,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bundled", result.stderr.casefold())

    def test_bootstrap_rejects_alternate_remote_and_local_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-bootstrap-") as temporary:
            base = pathlib.Path(temporary)
            repository = base / "repo"
            source_commit = self._fixture(repository)
            output = base / "divan.pyz"
            built = self._build(repository, output, source_commit)
            self.assertEqual(built.returncode, 0, built.stderr)
            for source in ("https://example.invalid/divan.git", str(repository)):
                with self.subTest(source=source):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(output),
                            "doctor",
                            "--host",
                            "codex",
                            "--source",
                            source,
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        check=False,
                        timeout=10,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("bundled source", result.stderr.casefold())


if __name__ == "__main__":
    unittest.main()
