"""Shared bounded subprocess and JSON helpers for eval adapters."""

from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
from typing import Any

MAX_INPUT_BYTES = 2_000_000
MAX_OUTPUT_BYTES = 2_000_000
PRIVATE_PATTERN = re.compile(
    r"(?i)(?:sk-[a-z0-9_-]{8,}|github_pat_[a-z0-9_]{8,}|gh[opusr]_[a-z0-9]{8,}|"
    r"(?:api[_-]?key|access[_-]?token|token|secret|password|passwd)\s*[=:]\s*[^\s,;]+|"
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"\b[A-Z]:\\Users\\[^\\/\s]+|/(?:home|Users)/[^/\s]+)"
)


class AdapterError(RuntimeError):
    """Safe, user-facing adapter error."""


def redact(text: str) -> str:
    return PRIVATE_PATTERN.sub("[REDACTED]", text)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise AdapterError("adapter input exceeds 2 MB")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"adapter input is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AdapterError("adapter input root must be an object")
    return value


def split_command(variable: str, default: str) -> list[str]:
    value = os.environ.get(variable, default)
    args = shlex.split(value, posix=sys.platform != "win32")
    if sys.platform == "win32":
        args = [
            arg[1:-1] if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in {'"', "'"} else arg
            for arg in args
        ]
    if not args:
        raise AdapterError(f"{variable} command is empty")
    return args


def timeout_seconds() -> float:
    try:
        value = float(os.environ.get("DIVAN_EVAL_TIMEOUT", "120"))
    except ValueError as exc:
        raise AdapterError("DIVAN_EVAL_TIMEOUT must be numeric") from exc
    if not 0 < value <= 1800:
        raise AdapterError("DIVAN_EVAL_TIMEOUT must be between 0 and 1800 seconds")
    return value


def run_command(
    args: list[str],
    *,
    cwd: pathlib.Path,
    stdin: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout or timeout_seconds(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdapterError(f"provider command did not complete: {redact(str(exc))}") from exc
    if len(completed.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise AdapterError("provider stdout exceeds 2 MB")
    if completed.returncode:
        detail = redact((completed.stderr or completed.stdout or "no diagnostics")[-2000:].strip())
        raise AdapterError(f"provider command failed with exit {completed.returncode}: {detail}")
    return completed


def parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AdapterError(f"{label} root must be an object")
    return value


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False))
