#!/usr/bin/env python3
"""Claude Code print-mode adapter for baseline-vs-selected-package evals."""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
from typing import Any

from common import AdapterError, emit, parse_json_object, read_payload, run_command, split_command

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _package_dir(payload: dict[str, Any]) -> pathlib.Path | None:
    condition = payload.get("condition")
    skill_name = payload.get("skill_name")
    skill_path = payload.get("skill_path")
    if condition not in {"baseline", "skill"}:
        raise AdapterError("condition must be baseline or skill")
    if not isinstance(skill_name, str) or not skill_name:
        raise AdapterError("skill_name is required")
    if condition == "baseline":
        if skill_path is not None:
            raise AdapterError("baseline must not receive skill_path")
        return None
    if not isinstance(skill_path, str) or not skill_path:
        raise AdapterError("skill condition requires skill_path")
    resolved = (ROOT / skill_path).resolve()
    plugins_root = (ROOT / "plugins").resolve()
    if not resolved.is_relative_to(plugins_root) or resolved.name != skill_name:
        raise AdapterError("skill_path escapes plugins or does not match skill_name")
    package = resolved.parent.parent
    if not (package / ".claude-plugin" / "plugin.json").is_file():
        raise AdapterError("selected skill package lacks Claude plugin manifest")
    return package


def run(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise AdapterError("prompt is required")
    package = _package_dir(payload)
    command = split_command("DIVAN_CLAUDE_BIN", "claude")
    args = [
        *command,
        "--print",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--setting-sources",
        "",
    ]
    model = os.environ.get("DIVAN_CLAUDE_MODEL")
    if model:
        args.extend(["--model", model])
    if package is not None:
        args.extend(["--plugin-dir", str(package)])
    args.append(prompt)
    with tempfile.TemporaryDirectory(prefix="divan-claude-agent-") as temporary:
        completed = run_command(args, cwd=pathlib.Path(temporary))
    response = parse_json_object(completed.stdout, "Claude output")
    output = response.get("result")
    if not isinstance(output, str) or not output.strip():
        raise AdapterError("Claude JSON output lacks a non-empty result")
    return {
        "output": output,
        "events": ["provider:claude-code"],
        "changed_files": [],
    }


def main() -> int:
    try:
        emit(run(read_payload()))
        return 0
    except AdapterError as exc:
        print(f"ADAPTER ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
