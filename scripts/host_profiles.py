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

import bootstrap_contract
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


def cli_failure_result(
    host: str, operation: str, error: str, cli_status: str
) -> dict[str, Any]:
    fallback = host == "codex" and cli_status in FALLBACK_CLI_STATUSES
    unavailable = cli_status in FALLBACK_CLI_STATUSES
    labels = {
        "missing": "CLI unavailable",
        "access-denied": "CLI access denied",
        "not-executable": "CLI not executable",
    }
    issue = labels.get(cli_status)
    if issue is None:
        prefix = f"{operation}: invalid JSON" if cli_status == "invalid-json" else operation
        issue = f"{prefix}: {error}"
    mode = FALLBACK_MODE if fallback else BLOCKED_MODE
    capability_mode = FALLBACK_MODE if fallback else NATIVE_MODE
    return {
        "status": "unavailable" if unavailable else "attention",
        "cli_status": cli_status,
        "recommended_mode": mode,
        "capabilities": capabilities(capability_mode),
        "issues": [issue],
    }


def next_command(
    options: Any,
    results: dict[str, dict[str, Any]],
    marketplace_list: Callable[[str], list[str]],
) -> str:
    codex = results.get("codex")
    if codex is not None and codex.get("cli_status") == "invalid-json":
        return subprocess.list2cmdline(marketplace_list("codex"))
    command = [
        *_cli_prefix(),
        "install",
        "--host",
        options.host,
        "--source",
        options.source,
        "--ref",
        options.ref,
    ]
    if codex is not None and codex.get("cli_status") in FALLBACK_CLI_STATUSES:
        command[command.index("--host") + 1] = "codex"
        command.extend(["--profile", "auto"])
    return subprocess.list2cmdline(command)


def _cli_prefix() -> list[str]:
    bundled = getattr(sys, "_divan_bootstrap_path", None)
    if isinstance(bundled, str) and pathlib.Path(bundled).is_file():
        return [sys.executable, bundled]
    return ["python", "scripts/divan.py"]


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


def _fallback_uninstall_command(root: pathlib.Path) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(root / "scripts" / "uninstall_codex.ps1"),
            "-Python",
            sys.executable,
        ]
    return [
        "bash",
        str(root / "scripts" / "uninstall_codex.sh"),
        "--python",
        sys.executable,
    ]


def rollback_command(root: pathlib.Path) -> list[str]:
    bundled = getattr(sys, "_divan_bootstrap_path", None)
    if isinstance(bundled, str) and pathlib.Path(bundled).is_file():
        return [sys.executable, bundled, "_fallback-remove"]
    return _fallback_uninstall_command(root)


def recovery_command(transaction: pathlib.Path) -> list[str]:
    return [*_cli_prefix(), "recover", str(transaction)]


def execute_fallback_remove(root: pathlib.Path) -> int:
    environment = os.environ.copy()
    environment["DIVAN_PYTHON"] = sys.executable
    result = host_probe.run(_fallback_uninstall_command(root), env=environment)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(
            result.stderr,
            end="" if result.stderr.endswith("\n") else "\n",
            file=sys.stderr,
        )
    return result.returncode


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
    try:
        bundled = bootstrap_contract.load(root)
    except bootstrap_contract.ContractError as error:
        raise ValueError(str(error)) from error
    if bundled is not None:
        return {
            skill for row in bundled[1].values() for skill in row["skills"]
        }
    return {
        path.parent.name
        for path in root.glob("plugins/*/skills/*/SKILL.md")
    }


def _single_manifest_value(
    rows: list[dict[str, str]],
    key: str,
    label: str,
    pattern: str | None = None,
) -> str:
    values = {str(row.get(key, "")) for row in rows}
    if len(values) != 1:
        raise ValueError(f"fallback manifest {label} is invalid")
    value = next(iter(values))
    if not value or (pattern is not None and not re.fullmatch(pattern, value)):
        raise ValueError(f"fallback manifest {label} is invalid")
    return value


def _manifest_identity(
    rows: list[dict[str, str]], options: Any
) -> tuple[str, str, str]:
    ref = _single_manifest_value(rows, "ref", "ref")
    if ref != options.ref:
        raise ValueError("fallback manifest ref does not match the requested ref")
    commit = _single_manifest_value(
        rows, "source_commit", "source commit", r"[0-9a-f]{40}"
    )
    archive = _single_manifest_value(
        rows, "archive_sha256", "archive checksum", r"[0-9a-f]{64}"
    )
    version = _single_manifest_value(rows, "surum", "version")
    return version, commit, archive


def _verified_skill_trees(
    rows: list[dict[str, str]], skills_dir: pathlib.Path
) -> dict[str, str]:
    installed: dict[str, str] = {}
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
    return installed


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
    version, commit, archive = _manifest_identity(rows, options)
    installed = _verified_skill_trees(rows, skills_dir)
    return {
        "manifest": str(manifest),
        "journal": str(journal),
        "skill_count": len(installed),
        "version": version,
        "source_commit": commit,
        "archive_sha256": archive,
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
    environment = _fallback_environment(options, root)
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


def _fallback_environment(options: Any, root: pathlib.Path) -> dict[str, str]:
    """Bind a standalone bootstrap fallback to its embedded immutable source."""
    try:
        return bootstrap_contract.fallback_environment(
            options,
            root,
            getattr(sys, "_divan_bootstrap_path", None),
            sys.executable,
        )
    except bootstrap_contract.ContractError as error:
        raise ValueError(str(error)) from error
