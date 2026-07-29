"""Safe host CLI process launch and diagnosis."""

from __future__ import annotations

import errno
import os
import pathlib
import shutil
import subprocess

_MARKER = "divan-cli-status:"
_CODES = {
    "not-executable": 125,
    "access-denied": 126,
    "missing": 127,
}


def _failure(
    command: list[str], status: str, detail: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        command,
        _CODES[status],
        "",
        f"{_MARKER}{status}: {detail}",
    )


def _os_error_status(exc: OSError) -> str:
    winerror = getattr(exc, "winerror", None)
    if isinstance(exc, FileNotFoundError) or exc.errno == errno.ENOENT:
        return "missing"
    if isinstance(exc, PermissionError) or exc.errno in {errno.EACCES, errno.EPERM}:
        return "access-denied"
    if winerror == 5:
        return "access-denied"
    if exc.errno == errno.ENOEXEC or winerror == 193:
        return "not-executable"
    return "not-executable"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a host command without allowing launch failures to escape."""
    resolved = shutil.which(command[0])
    if resolved is None:
        return _failure(command, "missing", f"executable not found: {command[0]}")
    actual = [resolved, *command[1:]]
    if os.name == "nt" and pathlib.Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        actual = ["cmd.exe", "/d", "/s", "/c", resolved, *command[1:]]
    try:
        return subprocess.run(
            actual,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        status = _os_error_status(exc)
        detail = exc.strerror or str(exc) or type(exc).__name__
        return _failure(command, status, detail)


def cli_status(result: subprocess.CompletedProcess[str]) -> str | None:
    """Return a stable launch status, or None for an ordinary CLI failure."""
    if result.returncode == 0:
        return "healthy"
    detail = result.stderr or result.stdout
    if detail.startswith(_MARKER):
        status = detail.removeprefix(_MARKER).split(":", 1)[0]
        if status in _CODES:
            return status
    return None

