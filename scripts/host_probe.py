"""Safe host CLI process launch and diagnosis."""

from __future__ import annotations

import errno
import os
import pathlib
import shutil
import subprocess
from collections.abc import Mapping

_MARKER = "divan-cli-status:"
_CODES = {
    "not-executable": 125,
    "access-denied": 126,
    "missing": 127,
}
_WINDOWS_SUFFIXES = (".cmd", ".exe", ".com", ".bat")


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


def resolve_executable(
    command: str,
    environment: Mapping[str, str] | None = None,
    *,
    windows: bool | None = None,
) -> str | None:
    """Resolve a host CLI without ever selecting a PowerShell script shim."""
    active = os.environ if environment is None else environment
    is_windows = os.name == "nt" if windows is None else windows
    if not is_windows:
        return shutil.which(command, path=active.get("PATH"))
    raw = pathlib.Path(command)
    suffix = raw.suffix.casefold()
    if suffix:
        if suffix not in _WINDOWS_SUFFIXES:
            return None
        resolved = shutil.which(command, path=active.get("PATH"))
        if (
            resolved
            and pathlib.Path(resolved).suffix.casefold() in _WINDOWS_SUFFIXES
        ):
            return resolved
        return None
    directories = [
        item for item in active.get("PATH", "").split(os.pathsep) if item
    ]
    appdata = active.get("APPDATA")
    if appdata:
        npm_home = str(pathlib.Path(appdata) / "npm")
        if npm_home not in directories:
            directories.append(npm_home)
    search_path = os.pathsep.join(directories)
    for extension in _WINDOWS_SUFFIXES:
        resolved = shutil.which(f"{command}{extension}", path=search_path)
        if resolved is not None:
            return resolved
    return None


def run(
    command: list[str],
    *,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a host command without allowing launch failures to escape."""
    resolved = resolve_executable(command[0], env)
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
            env=env,
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
