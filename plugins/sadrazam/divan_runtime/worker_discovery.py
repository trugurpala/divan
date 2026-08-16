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


def _candidate_roots(environ: dict[str, str]) -> list[Path]:
    """Where these CLIs land when they are not on PATH.

    Kept to documented install locations. No sweep of the whole profile, and
    no directory that holds credentials is opened.
    """
    roots: list[Path] = []
    local = environ.get("LOCALAPPDATA")
    roaming = environ.get("APPDATA")
    home = environ.get("USERPROFILE") or environ.get("HOME")
    if roaming:
        roots.append(Path(roaming) / "npm")
    if local:
        roots.append(Path(local) / "Programs")
        roots.append(Path(local) / "pnpm")
    if home:
        roots.append(Path(home) / ".local" / "bin")
        roots.append(Path(home) / "scoop" / "shims")
        roots.append(Path(home) / "bin")
    return roots


def _search_roots(command: str, roots: Iterable[Path]) -> tuple[str | None, list[str]]:
    searched: list[str] = []
    suffixes = ("", ".cmd", ".exe", ".ps1") if os.name == "nt" else ("",)
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
) -> WorkerProbe:
    """Find one worker, or prove it is genuinely absent.

    PATH is consulted through the repository's existing resolver rather than a
    second implementation, then the documented install roots are examined.
    """
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

    roots = _candidate_roots(active)
    searched: list[str] = ["PATH"]
    for command in commands:
        found, looked = _search_roots(command, roots)
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
) -> dict[str, WorkerProbe]:
    return {
        worker_id: probe_worker(worker_id, environ=environ, locator=locator)
        for worker_id in _WORKER_COMMANDS
    }
