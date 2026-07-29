"""Installation-profile decisions and capability contracts."""

from __future__ import annotations

import csv
import json
import os
import pathlib
import re
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import host_probe
import legacy_state

FALLBACK_CLI_STATUSES = {"missing", "not-executable", "access-denied"}
NATIVE_MODE = "native"
FALLBACK_MODE = "verified-skill-fallback"
BLOCKED_MODE = "blocked"

_CAPABILITIES = {
    NATIVE_MODE: {
        "skills": True,
        "instructions": True,
        "commands": True,
        "agents": True,
        "hooks": True,
        "mcp": True,
        "native_lifecycle": True,
    },
    FALLBACK_MODE: {
        "skills": True,
        "instructions": True,
        "commands": False,
        "agents": False,
        "hooks": False,
        "mcp": False,
        "native_lifecycle": False,
    },
}
FallbackRunner = Callable[
    [list[str], dict[str, str]], subprocess.CompletedProcess[str]
]


def capabilities(mode: str) -> dict[str, bool]:
    return dict(_CAPABILITIES[mode])


def select(host_result: dict[str, Any]) -> str:
    cli_status = host_result.get("cli_status")
    if cli_status == "healthy":
        return NATIVE_MODE
    if cli_status in FALLBACK_CLI_STATUSES:
        return FALLBACK_MODE
    return BLOCKED_MODE


def fallback_command(root: pathlib.Path) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(root / "scripts" / "install_codex.ps1"),
        ]
    return ["bash", str(root / "scripts" / "install_codex.sh")]


def rollback_command(root: pathlib.Path) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(root / "scripts" / "uninstall_codex.ps1"),
        ]
    return ["bash", str(root / "scripts" / "uninstall_codex.sh")]


def fallback_plan(options: Any, root: pathlib.Path, cli_status: str) -> dict[str, Any]:
    return {
        "schema": 1,
        "operation": "install",
        "status": "dry-run",
        "profile": "auto",
        "selected_mode": FALLBACK_MODE,
        "cli_status": cli_status,
        "source": options.source,
        "ref": options.ref,
        "capabilities": capabilities(FALLBACK_MODE),
        "environment": {"DIVAN_REF": options.ref},
        "planned_commands": [fallback_command(root)],
        "rollback_command": subprocess.list2cmdline(rollback_command(root)),
    }


def subprocess_fallback_runner(
    command: list[str], environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.update(environment)
    return host_probe.run(command, env=merged)


def _fallback_state_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("DIVAN_STATE_DIR", pathlib.Path.home() / ".codex")
    ).expanduser()


def _fallback_skills_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get(
            "CODEX_SKILLS_DIR", pathlib.Path.home() / ".codex" / "skills"
        )
    ).expanduser()


def _installer_payload(stdout: str) -> dict[str, Any]:
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("status") == "installed":
            return value
    raise ValueError("fallback installer did not return an installed manifest")


def _contained(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _expected_skill_names(root: pathlib.Path) -> set[str]:
    return {
        path.parent.name
        for path in root.glob("plugins/*/skills/*/SKILL.md")
    }


def _verify_manifest(
    options: Any,
    root: pathlib.Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    state_dir = _fallback_state_dir().resolve()
    skills_dir = _fallback_skills_dir().resolve()
    pointer = state_dir / "divan-install-latest"
    if not pointer.is_file():
        raise ValueError("fallback manifest pointer is missing")
    manifest = pathlib.Path(str(payload.get("manifest", ""))).expanduser().resolve()
    pointer_manifest = pathlib.Path(
        pointer.read_text(encoding="utf-8").strip()
    ).expanduser().resolve()
    if manifest != pointer_manifest or not _contained(manifest, state_dir):
        raise ValueError("fallback manifest pointer is outside the state directory")
    if not manifest.is_file():
        raise ValueError("fallback manifest is missing")
    journal = pathlib.Path(str(payload.get("journal", ""))).expanduser().resolve()
    if not journal.is_file() or not _contained(journal, state_dir):
        raise ValueError("fallback transaction journal is missing or untrusted")
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected = _expected_skill_names(root)
    if (
        len(expected) != 41
        or len(rows) != 41
        or {row.get("skill") for row in rows} != expected
    ):
        raise ValueError("fallback manifest does not contain exactly 41 Divan skills")
    installed: dict[str, str] = {}
    refs = {row.get("ref") for row in rows}
    commits = {row.get("source_commit") for row in rows}
    archives = {row.get("archive_sha256") for row in rows}
    versions = {row.get("surum") for row in rows}
    if refs != {options.ref}:
        raise ValueError("fallback manifest ref does not match the requested ref")
    if len(commits) != 1 or not re.fullmatch(r"[0-9a-f]{40}", str(next(iter(commits)))):
        raise ValueError("fallback manifest source commit is invalid")
    if len(archives) != 1 or not re.fullmatch(r"[0-9a-f]{64}", str(next(iter(archives)))):
        raise ValueError("fallback manifest archive checksum is invalid")
    if len(versions) != 1 or not next(iter(versions)):
        raise ValueError("fallback manifest version is invalid")
    for row in rows:
        name = str(row["skill"])
        target = pathlib.Path(str(row.get("hedef", ""))).expanduser().resolve()
        if target != (skills_dir / name).resolve() or not target.is_dir():
            raise ValueError(f"fallback skill target is invalid: {name}")
        checksum = str(row.get("installed_sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError(f"fallback skill checksum is invalid: {name}")
        if legacy_state.tree_digest(target) != checksum:
            raise ValueError(f"fallback skill checksum does not match: {name}")
        installed[name] = checksum
    return {
        "manifest": str(manifest),
        "journal": str(journal),
        "skill_count": len(installed),
        "version": str(next(iter(versions))),
        "source_commit": str(next(iter(commits))),
        "archive_sha256": str(next(iter(archives))),
        "installed_sha256": installed,
    }


def execute_fallback(
    options: Any,
    root: pathlib.Path,
    cli_status: str,
    runner: FallbackRunner,
) -> dict[str, Any]:
    if pathlib.Path(options.source).expanduser().exists():
        raise ValueError("auto fallback requires a checksum-backed release source")
    command = fallback_command(root)
    environment = {
        "DIVAN_REF": options.ref,
        "DIVAN_PYTHON": sys.executable,
    }
    result = runner(command, environment)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown fallback error").strip()
        raise ValueError(f"fallback installer failed ({result.returncode}): {detail}")
    payload = _installer_payload(result.stdout)
    verified = _verify_manifest(options, root, payload)
    return {
        "schema": 1,
        "operation": "install",
        "status": "verified",
        "profile": "auto",
        "selected_mode": FALLBACK_MODE,
        "cli_status": cli_status,
        "source": options.source,
        "ref": options.ref,
        "capabilities": capabilities(FALLBACK_MODE),
        "rollback_command": subprocess.list2cmdline(rollback_command(root)),
        "next_command": "Restart Codex, then open a new task.",
        **verified,
    }
