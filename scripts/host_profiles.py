"""Installation-profile decisions and capability contracts."""

from __future__ import annotations

import os
import pathlib
from typing import Any

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
        "rollback_command": (
            "powershell.exe -NoProfile -ExecutionPolicy Bypass "
            f"-File {root / 'scripts' / 'uninstall_codex.ps1'}"
            if os.name == "nt"
            else f"bash {root / 'scripts' / 'uninstall_codex.sh'}"
        ),
    }

