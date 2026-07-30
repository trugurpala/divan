#!/usr/bin/env python3
"""Run Divan's canonical hygiene-stable local verification sequence."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import timeouts  # noqa: E402

Command = tuple[str, ...]
CORE_COMMANDS: tuple[Command, ...] = (
    ("scripts/hygiene.py", "--check"),
    ("scripts/validate.py",),
    ("scripts/handoff.py", "--check"),
    ("scripts/catalog.py", "--check"),
    ("scripts/v1.py", "--check"),
    ("scripts/release.py", "--check"),
    ("evals/run.py", "--check"),
    ("-m", "unittest", "discover", "-s", "tests", "-v"),
    ("scripts/hygiene.py", "--check"),
)


def command_class(arguments: Command) -> str:
    """Map one fixed verification child to its bounded timeout class."""
    if arguments[:3] == ("-m", "unittest", "discover"):
        return "test"
    return "fast-check"


def verification_environment(
    root: pathlib.Path, cache_root: pathlib.Path
) -> dict[str, str]:
    """Return a child environment whose generated caches stay outside the repo."""
    resolved_root = root.resolve()
    resolved_cache = cache_root.resolve()
    if resolved_cache == resolved_root or resolved_cache.is_relative_to(resolved_root):
        raise ValueError("verification cache must be outside the repository")
    resolved_cache.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(resolved_cache / "python"),
            "RUFF_CACHE_DIR": str(resolved_cache / "ruff"),
            "MYPY_CACHE_DIR": str(resolved_cache / "mypy"),
            "COVERAGE_FILE": str(resolved_cache / "coverage"),
        }
    )
    return environment


def _run(
    root: pathlib.Path,
    commands: Sequence[Command],
    cache_root: pathlib.Path,
) -> int:
    environment = verification_environment(root, cache_root)
    verify_decision = timeouts.resolve_default("verify")
    deadline = time.monotonic() + verify_decision.configured_seconds
    for arguments in commands:
        child_decision = timeouts.resolve_default(command_class(arguments))
        remaining = max(0, deadline - time.monotonic())
        timeout_seconds = min(child_decision.configured_seconds, remaining)
        if timeout_seconds <= 0:
            print(
                "VERIFY TIMEOUT: overall verify limit reached "
                f"({verify_decision.configured_seconds}s)",
                file=sys.stderr,
                flush=True,
            )
            return 124
        printable = " ".join((sys.executable, "-B", *arguments))
        print(
            f"VERIFY [{command_class(arguments)} <= {timeout_seconds:.0f}s]: "
            f"{printable}",
            flush=True,
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-B", *arguments],
                cwd=root,
                env=environment,
                check=False,
                text=True,
                encoding="utf-8",
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            print(
                "VERIFY TIMEOUT: command exceeded its evidence-backed limit "
                f"({timeout_seconds:.0f}s): {printable}",
                file=sys.stderr,
                flush=True,
            )
            return 124
        if completed.returncode:
            return completed.returncode
    return 0


def run(
    root: pathlib.Path = ROOT,
    commands: Sequence[Command] = CORE_COMMANDS,
    cache_root: pathlib.Path | None = None,
) -> int:
    """Run commands in order and stop at the first failure."""
    if cache_root is not None:
        return _run(root.resolve(), commands, cache_root)
    with tempfile.TemporaryDirectory(prefix="divan-verify-") as temporary:
        return _run(root.resolve(), commands, pathlib.Path(temporary))


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
