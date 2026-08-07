from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.git_guard import (
    GitGuardError,
    commit_and_fast_forward,
    stage_review_snapshot,
)


def _git(directory: pathlib.Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(directory), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


def _project_with_worker(root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    project = root / "project"
    project.mkdir()
    _git(project, "init")
    _git(project, "config", "user.name", "Divan Test")
    _git(project, "config", "user.email", "divan-test@example.invalid")
    (project / "app.txt").write_text("before\n", encoding="utf-8")
    _git(project, "add", "app.txt")
    _git(project, "commit", "-m", "initial")

    worker = root / "worker"
    _git(
        project,
        "worktree",
        "add",
        "-b",
        "divan-guard-worker",
        str(worker),
        "HEAD",
    )
    (worker / "app.txt").write_text("after\n", encoding="utf-8")
    return project, worker


class GitGuardTests(unittest.TestCase):
    def test_reviewed_snapshot_fast_forwards_selected_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, worker = _project_with_worker(pathlib.Path(directory))
            snapshot = stage_review_snapshot(str(project), str(worker))

            merged = commit_and_fast_forward(
                str(project),
                snapshot,
                message="divan: approved change",
            )

            self.assertEqual(_git(project, "rev-parse", "HEAD"), merged.commit_sha)
            self.assertEqual(
                (project / "app.txt").read_text(encoding="utf-8"),
                "after\n",
            )
            self.assertEqual(merged.diff_sha256, snapshot.diff_sha256)

    def test_changed_staged_diff_requires_a_new_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, worker = _project_with_worker(pathlib.Path(directory))
            snapshot = stage_review_snapshot(str(project), str(worker))
            (worker / "app.txt").write_text("changed after review\n", encoding="utf-8")
            _git(worker, "add", "app.txt")

            with self.assertRaisesRegex(GitGuardError, "reviewed diff changed"):
                commit_and_fast_forward(
                    str(project),
                    snapshot,
                    message="must not merge",
                )

    def test_dirty_selected_project_blocks_merge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, worker = _project_with_worker(pathlib.Path(directory))
            snapshot = stage_review_snapshot(str(project), str(worker))
            (project / "local-note.txt").write_text("operator work\n", encoding="utf-8")

            with self.assertRaisesRegex(GitGuardError, "uncommitted changes"):
                commit_and_fast_forward(
                    str(project),
                    snapshot,
                    message="must not merge",
                )

    def test_project_head_change_requires_a_new_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project, worker = _project_with_worker(pathlib.Path(directory))
            snapshot = stage_review_snapshot(str(project), str(worker))
            (project / "operator.txt").write_text("new base\n", encoding="utf-8")
            _git(project, "add", "operator.txt")
            _git(project, "commit", "-m", "operator change")

            with self.assertRaisesRegex(GitGuardError, "HEAD changed after review"):
                commit_and_fast_forward(
                    str(project),
                    snapshot,
                    message="must not merge",
                )


if __name__ == "__main__":
    unittest.main()
