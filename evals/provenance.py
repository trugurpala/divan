"""Repository-bound provenance contracts for publishable eval runs."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from typing import Any

try:
    from evals.result_contracts import EvalError, _redact_public_text
except ModuleNotFoundError:  # Direct ``python evals/run.py`` execution.
    from result_contracts import EvalError, _redact_public_text  # type: ignore[no-redef]

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROVENANCE_REQUIRED_FIELDS = (
    "agent",
    "agent_version",
    "judge",
    "judge_version",
    "source_commit",
    "environment",
)


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvalError(f"{path}: JSON okunamadı: {error}") from error
    if not isinstance(value, dict):
        raise EvalError(f"{path}: kök JSON nesne olmalı")
    return value


def _read_provenance(path: pathlib.Path) -> dict[str, str]:
    """Read redacted runner provenance without accepting secret-like values."""
    data = _read_json(path)
    allowed = set(PROVENANCE_REQUIRED_FIELDS) | {"notes"}
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise EvalError(f"{path}: bilinmeyen provenance alanı: {', '.join(unexpected)}")
    provenance: dict[str, str] = {}
    for field in PROVENANCE_REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EvalError(f"{path}: provenance alanı eksik veya geçersiz: {field}")
        if _redact_public_text(value) != value:
            raise EvalError(f"{path}: provenance gizli/kişisel değer içeremez: {field}")
        provenance[field] = value.strip()
    if "notes" in data:
        notes = data["notes"]
        if not isinstance(notes, str) or not notes.strip():
            raise EvalError(f"{path}: provenance alanı eksik veya geçersiz: notes")
        if _redact_public_text(notes) != notes:
            raise EvalError(f"{path}: provenance gizli/kişisel değer içeremez: notes")
        provenance["notes"] = notes.strip()
    return provenance


def _repository_identity(root: pathlib.Path = ROOT) -> dict[str, str]:
    def git(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode:
            detail = _redact_public_text(completed.stderr.strip()) or "git failed"
            raise EvalError(f"repository identity cannot be derived: {detail}")
        return completed.stdout.strip()

    source_commit = git("rev-parse", "HEAD")
    if not re_full_commit(source_commit):
        raise EvalError("repository HEAD is not a full Git commit")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise EvalError("real eval requires a clean repository worktree")
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as error:
        raise EvalError("repository VERSION cannot be read") from error
    if not version:
        raise EvalError("repository VERSION is empty")
    return {"source_commit": source_commit, "divan_version": version}


def re_full_commit(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _version_for_command(variable: str, default: str) -> str:
    command_text = os.environ.get(variable, default)
    args = shlex.split(command_text, posix=sys.platform != "win32")
    if sys.platform == "win32":
        args = [
            item[1:-1]
            if len(item) >= 2 and item[0] == item[-1] and item[0] in {'"', "'"}
            else item
            for item in args
        ]
    resolved = shutil.which(args[0]) if args else None
    if resolved is None:
        raise EvalError(f"provider version executable cannot be found: {variable}")
    invocation = [resolved, *args[1:], "--version"]
    if os.name == "nt" and pathlib.Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        invocation = ["cmd.exe", "/d", "/s", "/c", resolved, *args[1:], "--version"]
    try:
        completed = subprocess.run(
            invocation,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise EvalError(f"provider version cannot be derived: {variable}") from error
    version = (completed.stdout or completed.stderr).strip().splitlines()
    if completed.returncode or not version:
        raise EvalError(f"provider version cannot be derived: {variable}")
    value = _redact_public_text(version[0])
    if value != version[0]:
        raise EvalError(f"provider version contains private data: {variable}")
    return value


def _bind_provenance(
    provenance: dict[str, str],
    *,
    provider_preset: str | None,
    seed: int | bytes = 0,
    selected_skills: list[str] | None = None,
    timeout: float = 120.0,
    min_skill_win_rate: float | None = None,
    root: pathlib.Path = ROOT,
    repository_identity: Callable[[pathlib.Path], dict[str, str]] = _repository_identity,
    version_for_command: Callable[[str, str], str] = _version_for_command,
) -> dict[str, str]:
    identity = repository_identity(root)
    if provenance["source_commit"] != identity["source_commit"]:
        raise EvalError("provenance source_commit does not match clean repository HEAD")
    bound = dict(provenance)
    bound.update(identity)
    bound["environment"] = "; ".join(
        filter(None, (platform.system(), platform.release(), platform.machine()))
    )
    if provider_preset == "claude-codex":
        bound.update(
            _provider_provenance(
                seed,
                selected_skills or [],
                timeout,
                min_skill_win_rate,
                version_for_command,
            )
        )
    return bound


def _provider_provenance(
    seed: int | bytes,
    selected_skills: list[str],
    timeout: float,
    min_skill_win_rate: float | None,
    version_for_command: Callable[[str, str], str],
) -> dict[str, str]:
    models = _provider_models()
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise EvalError("publishable provider runs require a 32-byte runner-generated seed")
    skills = sorted(selected_skills)
    command = ["python", "evals/run.py", "--run", "--provider-preset", "claude-codex"]
    for skill in skills:
        command.extend(["--skill", skill])
    command.extend(["--timeout", f"{timeout:g}"])
    if min_skill_win_rate is not None:
        command.extend(["--min-skill-win-rate", f"{min_skill_win_rate:g}"])
    return {
        "agent": "Claude Code",
        "agent_version": version_for_command("DIVAN_CLAUDE_BIN", "claude"),
        "judge": "Codex CLI",
        "judge_version": version_for_command("DIVAN_CODEX_BIN", "codex"),
        **models,
        "blind_seed_sha256": hashlib.sha256(seed).hexdigest(),
        "blind_seed_entropy_bits": "256",
        "blinding_method": "secrets.token_bytes(32)",
        "selected_skills": ",".join(skills),
        "timeout_seconds": f"{timeout:g}",
        "minimum_skill_win_rate": "none" if min_skill_win_rate is None else f"{min_skill_win_rate:g}",
        "run_command": subprocess.list2cmdline(command),
    }


def _provider_models() -> dict[str, str]:
    models: dict[str, str] = {}
    for variable, field in (
        ("DIVAN_CLAUDE_MODEL", "agent_model"),
        ("DIVAN_CODEX_MODEL", "judge_model"),
    ):
        value = os.environ.get(variable, "").strip()
        if not value:
            raise EvalError(f"{variable} must pin the provider model for publishable runs")
        if _redact_public_text(value) != value:
            raise EvalError(f"{variable} contains private data")
        models[field] = value
    return models
