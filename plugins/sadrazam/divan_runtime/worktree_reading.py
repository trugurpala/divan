"""Read back what a worker did to a worktree, and name the result.

Separated from execution on purpose. Starting a process and judging a diff are
different jobs, and the questions here are all about the tree: what changed,
whether this host may read it, and what the accepted work is called afterwards.

A sandboxed worker can create files the host has no permission to open. Staging
then fails, the diff comes back empty, and that looks exactly like a worker that
produced nothing. Every git call is therefore checked rather than assumed.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

#: Divan commits attempt results under its own name. The work was produced by
#: a worker under Divan's control, not typed by the owner, and a disposable
#: project may have no identity configured at all.
COMMITTER_NAME = "Divan"
COMMITTER_EMAIL = "attempt@divan.invalid"

#: How git reports a file it was not allowed to open.
_UNREADABLE_MARKER = 'error: open("'


@dataclass(frozen=True)
class WorktreeReading:
    """What the host could actually read back out of the worktree."""

    changed: tuple[str, ...]
    diff: str
    #: Files the worker wrote that the host is not permitted to read.
    unreadable: tuple[str, ...] = ()
    #: Why the read failed, when git would not name the files.
    read_error: str | None = None

    @property
    def readable(self) -> bool:
        return not self.unreadable and self.read_error is None


def git_in_worktree(worktree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one git command inside a worktree Divan owns."""
    return subprocess.run(
        ["git", "-C", str(worktree), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def worktree_snapshot(worktree: Path) -> str:
    """Fingerprint the tree without touching it.

    Taken before and after an attempt. A failed attempt leaves its work in the
    worktree and in the index, so a later attempt that changes nothing would
    otherwise find those files still listed and be credited with producing
    them, committing rejected work under an accepted attempt's name.
    """
    parts = (
        git_in_worktree(worktree, "status", "--porcelain").stdout,
        git_in_worktree(worktree, "diff").stdout,
        git_in_worktree(worktree, "diff", "--cached").stdout,
    )
    return "\n".join(parts)


def unreadable_paths(stderr: str) -> tuple[str, ...]:
    """Names of the files git was refused access to, as git reported them."""
    paths: list[str] = []
    for line in stderr.splitlines():
        start = line.find(_UNREADABLE_MARKER)
        if start == -1:
            continue
        rest = line[start + len(_UNREADABLE_MARKER):]
        end = rest.find('")')
        paths.append(rest if end == -1 else rest[:end])
    return tuple(paths)


def worktree_changes(worktree: Path) -> WorktreeReading:
    """Read back what the worker did, or report why it could not be read."""
    status = git_in_worktree(worktree, "status", "--porcelain")
    changed = tuple(
        line[3:].strip()
        for line in status.stdout.splitlines()
        if line.strip()
    )
    # Include untracked content so a newly created file counts as work.
    staged = git_in_worktree(worktree, "add", "-A")
    unreadable: tuple[str, ...] = ()
    read_error: str | None = None
    if staged.returncode != 0:
        unreadable = unreadable_paths(staged.stderr)
        if not unreadable:
            first = staged.stderr.strip().splitlines()
            read_error = first[0] if first else "git could not stage the worktree"
    diff = git_in_worktree(worktree, "diff", "--cached")
    return WorktreeReading(
        changed=changed,
        diff=diff.stdout,
        unreadable=unreadable,
        read_error=read_error,
    )


def commit_result(worktree: Path, attempt_id: str) -> str | None:
    """Give the accepted work an immutable name, or admit it has none."""
    committed = git_in_worktree(
        worktree,
        "-c",
        f"user.name={COMMITTER_NAME}",
        "-c",
        f"user.email={COMMITTER_EMAIL}",
        "commit",
        "-m",
        f"attempt {attempt_id}",
    )
    if committed.returncode != 0:
        return None
    head = git_in_worktree(worktree, "rev-parse", "HEAD")
    return head.stdout.strip() or None
