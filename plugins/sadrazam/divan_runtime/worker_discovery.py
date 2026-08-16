"""Establish whether a coding worker really exists on this machine.

"Not on PATH" is not the same finding as "not installed", and reporting the
first as the second sends an owner hunting for a problem that is really an
environment boundary. This module searches the places these CLIs actually
install into, records where it looked, and returns a finding that carries its
own evidence.

It never reads credentials. Authentication is observed only through a
capability the CLI itself reports, never by opening a token file.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable

from .executable_locator import locate_executable

WORKER_SCHEMA_VERSION = 1


class WorkerFinding(StrEnum):
    #: Resolved and its identity was confirmed.
    RESOLVED = "resolved"
    #: A launcher exists but could not be identified or run.
    UNUSABLE = "unusable"
    #: Nothing was found in any known location.
    ABSENT = "absent"


class LauncherPlatform(StrEnum):
    """Which platform's install layout a search should assume.

    Stated rather than inferred, so the Windows rules can be exercised on any
    machine. A test for winget discovery is then a test of the rule, not of
    the operating system the suite happens to be running on.
    """

    WINDOWS = "windows"
    POSIX = "posix"

    @classmethod
    def current(cls) -> LauncherPlatform:
        return cls.WINDOWS if os.name == "nt" else cls.POSIX


@dataclass(frozen=True)
class WorkerProbe:
    worker_id: str
    finding: WorkerFinding
    #: Absolute path when resolved, so the claim can be checked.
    executable: str | None = None
    #: Every location that was actually examined, so ABSENT means something.
    searched: tuple[str, ...] = ()
    detail: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = WORKER_SCHEMA_VERSION
        payload["finding"] = self.finding.value
        payload["searched"] = list(self.searched)
        payload["notes"] = list(self.notes)
        return payload


#: Launcher names each worker is published under, in preference order.
_WORKER_COMMANDS: dict[str, tuple[str, ...]] = {
    "codex": ("codex",),
    "claude": ("claude",),
}


def _windows_roots(environ: dict[str, str], home: str | None) -> list[Path]:
    """Documented Windows install locations, in the order they are examined."""
    roots: list[Path] = []
    roaming = environ.get("APPDATA")
    local = environ.get("LOCALAPPDATA")
    if roaming:
        roots.append(Path(roaming) / "npm")
    if local:
        roots.append(Path(local) / "Programs")
        roots.append(Path(local) / "pnpm")
        # winget installs each package into its own directory and only adds it
        # to the user PATH, so a process started before that refresh cannot see
        # it. Searching here turns a stale-PATH miss into a correct find.
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        roots.append(winget)
        roots.extend(_winget_package_dirs(winget))
    if home:
        roots.append(Path(home) / "scoop" / "shims")
    return roots


def _posix_roots(environ: dict[str, str], home: str | None) -> list[Path]:
    """Documented POSIX install locations."""
    roots: list[Path] = []
    if home:
        roots.append(Path(home) / ".npm-global" / "bin")
    roots.append(Path("/usr/local/bin"))
    return roots


def _candidate_roots(
    environ: dict[str, str], platform: LauncherPlatform
) -> list[Path]:
    """Where these CLIs land when they are not on PATH.

    Kept to documented install locations. No sweep of the whole profile, and
    no directory that holds credentials is opened.
    """
    home = environ.get("USERPROFILE") or environ.get("HOME")
    if platform is LauncherPlatform.WINDOWS:
        roots = _windows_roots(environ, home)
    else:
        roots = _posix_roots(environ, home)
    if home:
        # Used by both platforms.
        roots.append(Path(home) / ".local" / "bin")
        roots.append(Path(home) / "bin")
    return roots


def _winget_package_dirs(winget: Path) -> list[Path]:
    """Return winget package directories, and one level inside each.

    Some packages nest their launchers one directory deeper, as the Node
    package does. The walk stops there so this stays a bounded lookup rather
    than a sweep of the user profile.
    """
    if not winget.is_dir():
        return []
    found: list[Path] = []
    for package in sorted(winget.iterdir()):
        if not package.is_dir():
            continue
        found.append(package)
        found.extend(sorted(child for child in package.iterdir() if child.is_dir()))
    return found


#: What counts as a runnable launcher on each platform.
#: On Windows the extensionless file is a shell script that cannot run, and a
#: .ps1 shim is a script rather than a launcher, so real launchers come first
#: and the script forms are never eligible at all.
_LAUNCHER_SUFFIXES: dict[LauncherPlatform, tuple[str, ...]] = {
    LauncherPlatform.WINDOWS: (".cmd", ".exe", ".bat"),
    LauncherPlatform.POSIX: ("",),
}


def _search_roots(
    command: str, roots: Iterable[Path], platform: LauncherPlatform
) -> tuple[str | None, list[str]]:
    searched: list[str] = []
    suffixes = _LAUNCHER_SUFFIXES[platform]
    for root in roots:
        searched.append(str(root))
        if not root.is_dir():
            continue
        for suffix in suffixes:
            candidate = root / f"{command}{suffix}"
            if candidate.is_file():
                return str(candidate), searched
    return None, searched


def probe_worker(
    worker_id: str,
    *,
    environ: dict[str, str] | None = None,
    locator: Callable[[tuple[str, ...]], str | None] = locate_executable,
    platform: LauncherPlatform | None = None,
) -> WorkerProbe:
    """Find one worker, or prove it is genuinely absent.

    PATH is consulted through the repository's existing resolver rather than a
    second implementation, then the documented install roots are examined.
    """
    layout = platform or LauncherPlatform.current()
    commands = _WORKER_COMMANDS.get(worker_id)
    if commands is None:
        return WorkerProbe(
            worker_id=worker_id,
            finding=WorkerFinding.ABSENT,
            detail="unknown worker id",
        )

    active = dict(os.environ if environ is None else environ)
    resolved = locator(commands)
    if resolved:
        return WorkerProbe(
            worker_id=worker_id,
            finding=WorkerFinding.RESOLVED,
            executable=resolved,
            searched=("PATH",),
        )

    roots = _candidate_roots(active, layout)
    searched: list[str] = ["PATH"]
    for command in commands:
        found, looked = _search_roots(command, roots, layout)
        searched.extend(looked)
        if found:
            return WorkerProbe(
                worker_id=worker_id,
                finding=WorkerFinding.RESOLVED,
                executable=found,
                searched=tuple(dict.fromkeys(searched)),
                notes=("resolved outside PATH; this is an environment boundary",),
            )

    return WorkerProbe(
        worker_id=worker_id,
        finding=WorkerFinding.ABSENT,
        searched=tuple(dict.fromkeys(searched)),
        detail=f"{worker_id} was not found in PATH or any known install root",
    )


def probe_all(
    *,
    environ: dict[str, str] | None = None,
    locator: Callable[[tuple[str, ...]], str | None] = locate_executable,
    platform: LauncherPlatform | None = None,
) -> dict[str, WorkerProbe]:
    return {
        worker_id: probe_worker(
            worker_id, environ=environ, locator=locator, platform=platform
        )
        for worker_id in _WORKER_COMMANDS
    }
