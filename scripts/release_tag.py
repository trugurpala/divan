#!/usr/bin/env python3
"""Resolve one live remote release tag to its immutable commit."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable

SHA40 = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
Run = Callable[[list[str]], subprocess.CompletedProcess[str]]


class ReleaseTagError(RuntimeError):
    """Raised when a remote release tag cannot be proven exactly."""


def _git(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def resolve_remote_tag(
    remote: str,
    tag: str,
    *,
    run: Run = _git,
) -> str | None:
    """Return the peeled commit for an exact remote tag, or None if absent."""
    if not remote or not TAG.fullmatch(tag):
        raise ReleaseTagError("remote and SemVer release tag are required")
    direct_ref = f"refs/tags/{tag}"
    peeled_ref = f"{direct_ref}^{{}}"
    completed = run(
        [
            "git",
            "ls-remote",
            "--tags",
            remote,
            direct_ref,
            peeled_ref,
        ]
    )
    if completed.returncode != 0:
        raise ReleaseTagError(
            "cannot read remote release tag "
            f"(git ls-remote exited with status {completed.returncode})"
        )

    rows: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] not in {direct_ref, peeled_ref}:
            raise ReleaseTagError("remote release tag response is invalid")
        commit, ref = fields
        if not SHA40.fullmatch(commit) or ref in rows:
            raise ReleaseTagError("remote release tag response is invalid")
        rows[ref] = commit
    if not rows:
        return None
    if direct_ref not in rows:
        raise ReleaseTagError("remote release tag object is missing")
    return rows.get(peeled_ref, rows[direct_ref])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--tag", required=True)
    options = parser.parse_args()
    try:
        commit = resolve_remote_tag(options.remote, options.tag)
    except ReleaseTagError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if commit is not None:
        print(commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
