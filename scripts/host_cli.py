"""Human-facing host lifecycle command dispatch and output."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

import host_options
import host_profiles


def _recover(arguments: list[str], lifecycle: Any) -> int | None:
    requested = any(
        argument == "--rollback-transaction"
        or argument.startswith("--rollback-transaction=")
        for argument in arguments
    )
    if not requested:
        return None
    parser = argparse.ArgumentParser(description="Recover an interrupted Divan install")
    parser.add_argument("--rollback-transaction", type=pathlib.Path, required=True)
    recovery = parser.parse_args(arguments)
    try:
        record = lifecycle["rollback_transaction"](recovery.rollback_transaction)
    except lifecycle["InstallError"] as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    print(f"RECOVERED - transaction: {record['transaction_path']}")
    return 0


def _dispatch(options: host_options.Options, lifecycle: Any) -> dict[str, Any]:
    if options.doctor:
        return lifecycle["doctor"](options)
    if options.upgrade:
        return lifecycle["upgrade"](options)
    return lifecycle["install"](options)


def _print_doctor(record: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(record, ensure_ascii=False))
        return
    for host, result in record["hosts"].items():
        suffix = "" if not result["issues"] else " - " + "; ".join(result["issues"])
        print(f"{host}: {result['status']}{suffix}")
    host_issues = {
        issue for result in record["hosts"].values() for issue in result["issues"]
    }
    aggregate = [issue for issue in record["issues"] if issue not in host_issues]
    if aggregate:
        print(f"STATUS: {record['status']} - {'; '.join(aggregate)}")
    if record["status"] == "healthy":
        print(
            "READY: Divan is installed and verified. "
            "Start a new agent session and describe your goal."
        )
        return
    print(f"NEXT: {record['next_command']}")


def _print_install(record: dict[str, Any]) -> None:
    if record["status"] == "dry-run":
        print("DRY-RUN - no host state changed. Add --execute to apply:")
        for command in record["planned_commands"]:
            print("  " + subprocess.list2cmdline(command))
        return
    if record["status"] == "no-op":
        print("NO-OP - installed Divan already matches target.")
        return
    if record.get("selected_mode") != host_profiles.FALLBACK_MODE:
        print(f"VERIFIED - transaction: {record['transaction_path']}")
        return
    print(
        "VERIFIED SKILL FALLBACK "
        f"- {record['skill_count']}/42 skills; manifest: {record['manifest']}"
    )
    print(
        "CAPABILITIES - skills/instructions available; "
        "native commands, agents, hooks, MCP, and lifecycle unavailable."
    )
    print(f"ROLLBACK: {record['rollback_command']}")
    print(f"NEXT: {record['next_command']}")


def main(argv: list[str] | None, lifecycle: Any) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    recovery_status = _recover(arguments, lifecycle)
    if recovery_status is not None:
        return recovery_status
    options = host_options.parse_options(arguments)
    try:
        record = _dispatch(options, lifecycle)
    except lifecycle["InstallError"] as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    if options.doctor:
        _print_doctor(record, options.json_output)
    else:
        _print_install(record)
    return 0
