"""Certify a coding worker from what it actually does, not from its presence.

A resolved executable proves nothing. This module runs bounded, non-interactive
probes and reports only what they observed: the launcher's own version, and the
authentication state the CLI reports about itself.

No credential file is ever opened and no login flow is ever started. If a CLI
will not say whether it is signed in, the answer is unknown, not assumed.
"""
from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Sequence

from .worker_discovery import WorkerFinding, WorkerProbe, probe_worker

CERTIFICATION_SCHEMA_VERSION = 1

#: Probes must never hang a health check.
PROBE_TIMEOUT_SECONDS = 45


class AuthState(StrEnum):
    AUTHENTICATED = "authenticated"
    NOT_AUTHENTICATED = "not-authenticated"
    #: The CLI ran but did not say. Never treated as authenticated.
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WorkerCertificate:
    worker_id: str
    executable: str | None
    version: str | None
    auth: AuthState
    #: Exact text the probe matched on, so the verdict can be checked.
    auth_evidence: str | None = None
    notes: tuple[str, ...] = ()

    @property
    def certified(self) -> bool:
        return (
            self.executable is not None
            and self.version is not None
            and self.auth is AuthState.AUTHENTICATED
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = CERTIFICATION_SCHEMA_VERSION
        payload["auth"] = self.auth.value
        payload["certified"] = self.certified
        payload["notes"] = list(self.notes)
        return payload


def _run(argv: Sequence[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


#: How each CLI reports that it is signed in. Matched against combined output.
_AUTH_PROBES: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    # worker: (argv suffix, phrases meaning signed in, phrases meaning signed out)
    "codex": (
        ("login", "status"),
        ("logged in",),
        ("not logged in", "please run", "login required"),
    ),
    "claude": (
        ("doctor",),
        ("subscription auth active",),
        ("not signed in", "not logged in", "please run"),
    ),
}


def _read_version(executable: str) -> str | None:
    """Ask the launcher its own version, or admit it did not answer."""
    result = _run([executable, "--version"])
    if result is None or result.returncode != 0:
        return None
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0].strip() if lines else None


def _read_auth(worker_id: str, executable: str) -> tuple[AuthState, str | None]:
    """Ask the CLI whether it is signed in. Signed-out always wins."""
    spec = _AUTH_PROBES.get(worker_id)
    if spec is None:
        return AuthState.UNKNOWN, None
    argv_suffix, signed_in, signed_out = spec
    result = _run([executable, *argv_suffix])
    if result is None:
        return AuthState.UNKNOWN, None
    combined = f"{result.stdout}\n{result.stderr}".casefold()
    for phrase in signed_out:
        if phrase in combined:
            return AuthState.NOT_AUTHENTICATED, phrase
    for phrase in signed_in:
        if phrase in combined:
            return AuthState.AUTHENTICATED, phrase
    return AuthState.UNKNOWN, None


def certify_worker(worker_id: str, *, probe: WorkerProbe | None = None) -> WorkerCertificate:
    """Establish what this worker can actually do right now."""
    found = probe or probe_worker(worker_id)
    if found.finding is not WorkerFinding.RESOLVED or not found.executable:
        return WorkerCertificate(
            worker_id=worker_id,
            executable=None,
            version=None,
            auth=AuthState.UNKNOWN,
            notes=(found.detail or "worker was not resolved",),
        )

    executable = found.executable
    notes: list[str] = list(found.notes)

    version = _read_version(executable)
    if version is None:
        notes.append("launcher did not report a version")

    auth, auth_evidence = _read_auth(worker_id, executable)
    if auth is AuthState.UNKNOWN and worker_id in _AUTH_PROBES:
        notes.append("authentication state could not be read from the CLI")

    return WorkerCertificate(
        worker_id=worker_id,
        executable=executable,
        version=version,
        auth=auth,
        auth_evidence=auth_evidence,
        notes=tuple(notes),
    )
