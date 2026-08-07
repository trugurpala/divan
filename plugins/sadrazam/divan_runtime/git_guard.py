from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

GitRunner = Callable[[Sequence[str], Path | None, float], tuple[int, str, str]]


class GitGuardError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewSnapshot:
    worktree: str
    base_head: str
    diff_sha256: str
    diff: str

    def metadata(self) -> dict[str, str]:
        return {
            "worktree": self.worktree,
            "base_head": self.base_head,
            "diff_sha256": self.diff_sha256,
        }


@dataclass(frozen=True)
class MergeResult:
    commit_sha: str
    base_head: str
    diff_sha256: str


def stage_review_snapshot(
    project_root: str,
    worktree: str,
    *,
    runner: GitRunner | None = None,
) -> ReviewSnapshot:
    active_runner = runner or _run
    project = _directory(project_root, "project_root")
    worker = _directory(worktree, "worktree")
    _require_same_repository(project, worker, active_runner)
    base_head = _git_text(worker, ("rev-parse", "HEAD"), active_runner, 15.0)
    _git_ok(worker, ("add", "-A", "--"), active_runner, 60.0)
    diff = _git_text(
        worker,
        ("diff", "--cached", "--binary", "--no-ext-diff", "--"),
        active_runner,
        60.0,
        allow_empty=True,
    )
    if not diff.strip():
        raise GitGuardError("task has no staged changes to review")
    return ReviewSnapshot(
        worktree=str(worker),
        base_head=base_head,
        diff_sha256=_sha256(diff),
        diff=diff,
    )


def commit_and_fast_forward(
    project_root: str,
    snapshot: ReviewSnapshot,
    *,
    message: str,
    runner: GitRunner | None = None,
) -> MergeResult:
    active_runner = runner or _run
    project = _directory(project_root, "project_root")
    worker = _directory(snapshot.worktree, "worktree")
    _require_same_repository(project, worker, active_runner)
    status = _git_text(
        project,
        ("status", "--porcelain", "--untracked-files=normal"),
        active_runner,
        15.0,
        allow_empty=True,
    )
    if status.strip():
        raise GitGuardError("project has uncommitted changes; merge is blocked")
    project_head = _git_text(project, ("rev-parse", "HEAD"), active_runner, 15.0)
    if project_head != snapshot.base_head:
        raise GitGuardError("project HEAD changed after review; review must run again")
    current_diff = _git_text(
        worker,
        ("diff", "--cached", "--binary", "--no-ext-diff", "--"),
        active_runner,
        60.0,
        allow_empty=True,
    )
    if _sha256(current_diff) != snapshot.diff_sha256:
        raise GitGuardError("reviewed diff changed after review; review must run again")
    if not current_diff.strip():
        raise GitGuardError("reviewed diff is empty")
    commit_message = message.strip()[:200] or "Divan approved task"
    _git_ok(worker, ("commit", "-m", commit_message), active_runner, 120.0)
    commit_sha = _git_text(worker, ("rev-parse", "HEAD"), active_runner, 15.0)
    project_head = _git_text(project, ("rev-parse", "HEAD"), active_runner, 15.0)
    if project_head != snapshot.base_head:
        raise GitGuardError(
            "project HEAD changed while approval was running; fast-forward is blocked"
        )
    _git_ok(project, ("merge", "--ff-only", commit_sha), active_runner, 120.0)
    return MergeResult(
        commit_sha=commit_sha,
        base_head=snapshot.base_head,
        diff_sha256=snapshot.diff_sha256,
    )


def snapshot_from_metadata(value: object) -> ReviewSnapshot:
    if not isinstance(value, dict):
        raise GitGuardError("task has no reviewed Git snapshot")
    worktree = value.get("worktree")
    base_head = value.get("base_head")
    diff_sha256 = value.get("diff_sha256")
    if not isinstance(worktree, str) or not worktree.strip():
        raise GitGuardError("persisted reviewed Git snapshot is invalid")
    if not isinstance(base_head, str) or not base_head.strip():
        raise GitGuardError("persisted reviewed Git snapshot is invalid")
    if not isinstance(diff_sha256, str) or not diff_sha256.strip():
        raise GitGuardError("persisted reviewed Git snapshot is invalid")
    return ReviewSnapshot(
        worktree=worktree.strip(),
        base_head=base_head.strip(),
        diff_sha256=diff_sha256.strip(),
        diff="",
    )


def _directory(value: str, field: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise GitGuardError(f"{field} must be an existing directory")
    return path


def _require_same_repository(project: Path, worktree: Path, runner: GitRunner) -> None:
    project_common = _common_git_dir(project, runner)
    worktree_common = _common_git_dir(worktree, runner)
    if project_common != worktree_common:
        raise GitGuardError("execution worktree does not belong to the selected project")


def _common_git_dir(directory: Path, runner: GitRunner) -> Path:
    raw = _git_text(directory, ("rev-parse", "--git-common-dir"), runner, 15.0)
    path = Path(raw)
    if not path.is_absolute():
        path = directory / path
    return path.resolve()


def _git_ok(
    directory: Path,
    args: Sequence[str],
    runner: GitRunner,
    timeout: float,
) -> None:
    code, stdout, stderr = runner(("git", "-C", str(directory), *args), None, timeout)
    if code != 0:
        detail = (stderr or stdout).strip()[:500]
        raise GitGuardError(detail or f"git command failed with exit code {code}")


def _git_text(
    directory: Path,
    args: Sequence[str],
    runner: GitRunner,
    timeout: float,
    *,
    allow_empty: bool = False,
) -> str:
    code, stdout, stderr = runner(("git", "-C", str(directory), *args), None, timeout)
    if code != 0:
        detail = (stderr or stdout).strip()[:500]
        raise GitGuardError(detail or f"git command failed with exit code {code}")
    text = stdout.rstrip("\r\n")
    if not allow_empty and not text:
        raise GitGuardError("git command returned no output")
    return text


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _run(
    argv: Sequence[str],
    cwd: Path | None,
    timeout: float,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "git command timed out"
    except OSError as error:
        return 127, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr