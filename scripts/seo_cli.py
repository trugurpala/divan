"""Command-line surface for local SEO audit and explicit GitHub verification."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

from seo import audit_project, load_policy, verify_github


def _read_config(path: pathlib.Path | None) -> Any:
    if path is None:
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("configuration must be a regular non-symlink file")
    if path.stat().st_size > load_policy()["limits"]["max_file_bytes"]:
        raise ValueError("configuration exceeds the file size limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("configuration must be valid UTF-8 JSON") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit")
    audit.add_argument("--project", type=pathlib.Path, required=True)
    audit.add_argument("--profile", choices=("standard", "strict"), default="standard")
    audit.add_argument("--evidence", type=pathlib.Path)
    audit.add_argument("--search-console-config", type=pathlib.Path)
    audit.add_argument("--expected-url")
    audit.add_argument("--json", action="store_true", required=True)
    verify = commands.add_parser("verify-github")
    verify.add_argument("--project", type=pathlib.Path, required=True)
    verify.add_argument("--profile", choices=("standard", "strict"), default="standard")
    verify.add_argument("--repository")
    verify.add_argument("--run-id", required=True)
    verify.add_argument("--run-attempt", type=int, required=True)
    verify.add_argument("--workflow-commit", required=True)
    verify.add_argument("--expected-url")
    verify.add_argument("--json", action="store_true", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "audit":
            result = audit_project(
                args.project,
                args.profile,
                evidence=_read_config(args.evidence),
                search_console=_read_config(args.search_console_config),
                expected_url=args.expected_url,
            )
        else:
            result = verify_github(
                args.project,
                repository=args.repository,
                run_id=args.run_id,
                run_attempt=args.run_attempt,
                workflow_commit=args.workflow_commit,
                expected_url=args.expected_url,
                profile=args.profile,
            )
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"PASS", "NOT_APPLICABLE"} else 1
