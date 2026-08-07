#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Mapping, Sequence

AUTH_MARKER = "DIVAN_AUTH_OK"


class AgentPreflightError(RuntimeError):
    pass


def _run(
    argv: Sequence[str], *, timeout: float, stdin_text: str | None = None
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(argv),
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr)
        return 124, stdout, stderr or "command timed out"
    except OSError as error:
        return 127, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def _timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def parse_codex_auth(text: str) -> str:
    normalized = text.casefold()
    states = (
        ("logged in using chatgpt", "chatgpt"),
        ("logged in using an api key", "api-key"),
        ("logged in using agent identity", "agent-identity"),
    )
    if "not logged in" in normalized:
        raise AgentPreflightError("Codex is installed but not authenticated")
    for marker, method in states:
        if marker in normalized:
            return method
    raise AgentPreflightError("Codex authentication status is unknown")


def _codex_message_text(event: Mapping[str, object]) -> str | None:
    item = event.get("item")
    if isinstance(item, Mapping):
        text = item.get("text")
        if isinstance(text, str):
            return text
    message = event.get("message")
    return message if isinstance(message, str) else None


def parse_codex_probe(stdout: str) -> None:
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        message = _codex_message_text(event)
        if message is not None:
            if message.strip() == AUTH_MARKER:
                return
            raise AgentPreflightError(
                "Codex session probe did not return the expected marker"
            )
    raise AgentPreflightError("Codex session probe returned no final message")


def parse_claude_probe(stdout: str) -> None:
    try:
        payload = json.loads(stdout.strip())
    except json.JSONDecodeError as error:
        raise AgentPreflightError(
            "Claude Code did not return JSON during auth probe"
        ) from error
    if not isinstance(payload, dict):
        raise AgentPreflightError(
            "Claude Code auth probe response is not a JSON object"
        )
    result = payload.get("result")
    if not isinstance(result, str) or result.strip() != AUTH_MARKER:
        raise AgentPreflightError(
            "Claude Code auth probe did not return the expected marker"
        )


def preflight() -> dict[str, object]:
    codex = shutil.which("codex")
    claude = shutil.which("claude")
    if not codex:
        raise AgentPreflightError("Codex is not available on PATH")
    if not claude:
        raise AgentPreflightError("Claude Code is not available on PATH")

    code, stdout, stderr = _run((codex, "login", "status"), timeout=15.0)
    codex_text = f"{stdout}\n{stderr}".strip()
    if code != 0:
        raise AgentPreflightError("Codex login status probe failed")
    codex_method = parse_codex_auth(codex_text)

    prompt = (
        f"Return exactly {AUTH_MARKER}. "
        "Do not use tools, edit files, or run commands."
    )
    code, stdout, _ = _run(
        (
            codex,
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "-",
        ),
        timeout=45.0,
        stdin_text=prompt,
    )
    if code != 0:
        raise AgentPreflightError("Codex authenticated session probe failed")
    parse_codex_probe(stdout)

    code, stdout, _ = _run(
        (
            claude,
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--max-turns",
            "1",
        ),
        timeout=45.0,
        stdin_text=prompt,
    )
    if code != 0:
        raise AgentPreflightError("Claude Code authenticated session probe failed")
    parse_claude_probe(stdout)

    return {
        "schema_version": 1,
        "status": "pass",
        "codex": {"authenticated": True, "method": codex_method},
        "claude": {"authenticated": True, "method": "read-only-session-probe"},
    }


def main() -> int:
    try:
        result = preflight()
    except AgentPreflightError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
