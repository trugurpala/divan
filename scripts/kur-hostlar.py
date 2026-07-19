#!/usr/bin/env python3
"""Divan'i Claude ve Codex'e resmi plugin CLI'lariyla islemesel olarak kur."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

PACKAGES = ("sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack")
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class InstallError(RuntimeError):
    """Raised after a failed installation has been rolled back."""


class Options:
    def __init__(
        self,
        *,
        host: str,
        source: str,
        ref: str,
        execute: bool,
        migrate_legacy: bool,
        state_dir: pathlib.Path,
    ) -> None:
        self.host = host
        self.source = source
        self.ref = ref
        self.execute = execute
        self.migrate_legacy = migrate_legacy
        self.state_dir = state_dir


def _subprocess_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _run(runner: Runner, command: list[str]) -> str:
    result = runner(command)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown CLI error").strip()
        raise InstallError(f"command failed ({result.returncode}): {' '.join(command)}: {detail}")
    return result.stdout


def _read_json(runner: Runner, command: list[str]) -> Any:
    output = _run(runner, command)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise InstallError(f"host CLI returned invalid JSON for {' '.join(command)}: {exc}") from exc


def _marketplaces(host: str, runner: Runner) -> set[str]:
    value = _read_json(runner, [host, "plugin", "marketplace", "list", "--json"])
    rows = value if host == "claude" else value.get("marketplaces", [])
    return {
        row["name"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }


def _plugins(host: str, runner: Runner) -> set[str]:
    value = _read_json(runner, [host, "plugin", "list", "--json"])
    rows = value if host == "claude" else value.get("installed", [])
    key = "id" if host == "claude" else "pluginId"
    return {
        row[key]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get(key), str)
    }


def _hosts(selection: str) -> tuple[str, ...]:
    return ("claude", "codex") if selection == "both" else (selection,)


def _add_marketplace_command(host: str, source: str, ref: str) -> list[str]:
    if host == "claude":
        return ["claude", "plugin", "marketplace", "add", f"{source}#{ref}"]
    return ["codex", "plugin", "marketplace", "add", source, "--ref", ref, "--json"]


def _install_command(host: str, package: str) -> list[str]:
    selector = f"{package}@divan"
    if host == "claude":
        return ["claude", "plugin", "install", selector, "--scope", "user"]
    return ["codex", "plugin", "add", selector, "--json"]


def _remove_plugin_command(host: str, selector: str) -> list[str]:
    if host == "claude":
        return ["claude", "plugin", "uninstall", selector, "--scope", "user", "--yes"]
    return ["codex", "plugin", "remove", selector, "--json"]


def _remove_marketplace_command(host: str) -> list[str]:
    return [host, "plugin", "marketplace", "remove", "divan"] + (
        ["--json"] if host == "codex" else []
    )


def _planned_commands(options: Options) -> list[list[str]]:
    commands: list[list[str]] = []
    for host in _hosts(options.host):
        commands.append(_add_marketplace_command(host, options.source, options.ref))
        commands.extend(_install_command(host, package) for package in PACKAGES)
    return commands


def _persist_record(path: pathlib.Path, record: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _begin_mutation(
    path: pathlib.Path, record: dict[str, Any], pending: dict[str, str]
) -> None:
    record["pending"] = pending
    _persist_record(path, record)


def _finish_mutation(path: pathlib.Path, record: dict[str, Any]) -> None:
    record["pending"] = None
    _persist_record(path, record)


def _migrate_legacy(root: pathlib.Path, runner: Runner) -> list[str] | None:
    state_dir = pathlib.Path(os.environ.get("DIVAN_STATE_DIR", pathlib.Path.home() / ".codex"))
    pointer = state_dir / "divan-install-latest"
    manifest: pathlib.Path | None = None
    if pointer.is_file():
        candidate = pathlib.Path(pointer.read_text(encoding="utf-8").strip())
        manifest = candidate if candidate.is_file() else None
    if manifest is None:
        candidates = sorted(state_dir.glob("divan-install-*.tsv"), key=lambda path: path.stat().st_mtime)
        manifest = candidates[-1] if candidates else None
    if manifest is None:
        return None
    if os.name == "nt":
        command = [
            "powershell",
            "-NoProfile",
            "-File",
            str(root / "scripts" / "kaldir-codex.ps1"),
            "-Manifest",
            str(manifest),
        ]
    else:
        command = ["bash", str(root / "scripts" / "kaldir-codex.sh"), str(manifest)]
    _run(runner, command)
    return command


def rollback_transaction(
    transaction_path: pathlib.Path,
    *,
    runner: Runner = _subprocess_runner,
) -> dict[str, Any]:
    """Recover an interrupted transaction using only entries absent from pre-state."""
    try:
        record = json.loads(transaction_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"transaction journal is unreadable: {transaction_path}") from exc
    if not isinstance(record, dict) or record.get("schema") != 1:
        raise InstallError("unsupported transaction journal schema")
    if record.get("status") not in {"in-progress", "rollback-incomplete", "verified"}:
        raise InstallError(f"transaction is not recoverable: {record.get('status')}")

    before = record.get("before")
    created = record.get("created")
    if not isinstance(before, dict) or not isinstance(created, dict):
        raise InstallError("transaction journal lacks ownership state")

    plugin_rows = list(created.get("plugins", []))
    marketplace_hosts = list(created.get("marketplaces", []))
    pending = record.get("pending")
    if isinstance(pending, dict) and pending.get("kind") == "plugin":
        plugin_rows.append({"host": pending.get("host"), "id": pending.get("id")})
    elif isinstance(pending, dict) and pending.get("kind") == "marketplace":
        marketplace_hosts.append(pending.get("host"))

    owned_plugins: list[dict[str, str]] = []
    for row in plugin_rows:
        if not isinstance(row, dict):
            raise InstallError("transaction contains an invalid plugin entry")
        host, selector = row.get("host"), row.get("id")
        if host not in {"claude", "codex"} or not isinstance(selector, str):
            raise InstallError("transaction contains an invalid plugin identity")
        if not selector.endswith("@divan"):
            raise InstallError("transaction refuses to remove a non-Divan plugin")
        host_before = before.get(host, {})
        if selector in host_before.get("plugins", []):
            raise InstallError(f"transaction does not own pre-existing plugin: {selector}")
        if row not in owned_plugins:
            owned_plugins.append({"host": host, "id": selector})

    owned_marketplaces: list[str] = []
    for host in marketplace_hosts:
        if host not in {"claude", "codex"}:
            raise InstallError("transaction contains an invalid marketplace host")
        host_before = before.get(host, {})
        if "divan" in host_before.get("marketplaces", []):
            raise InstallError(f"transaction does not own pre-existing marketplace: {host}")
        if host not in owned_marketplaces:
            owned_marketplaces.append(host)

    record["status"] = "recovering"
    _persist_record(transaction_path, record)
    for plugin in reversed(owned_plugins):
        if plugin["id"] in _plugins(plugin["host"], runner):
            _begin_mutation(
                transaction_path,
                record,
                {"kind": "recovery-plugin", **plugin},
            )
            _run(runner, _remove_plugin_command(plugin["host"], plugin["id"]))
            _finish_mutation(transaction_path, record)
    for host in reversed(owned_marketplaces):
        if "divan" in _marketplaces(host, runner):
            _begin_mutation(
                transaction_path,
                record,
                {"kind": "recovery-marketplace", "host": host},
            )
            _run(runner, _remove_marketplace_command(host))
            _finish_mutation(transaction_path, record)
    record["status"] = "recovered"
    record["pending"] = None
    record["recovered_at"] = datetime.now(UTC).isoformat()
    _persist_record(transaction_path, record)
    return record


def install(
    options: Options,
    *,
    runner: Runner = _subprocess_runner,
    root: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Plan or execute installation and return the auditable transaction record."""
    if options.migrate_legacy and "codex" not in _hosts(options.host):
        raise InstallError("legacy Codex migration requires --host codex or --host both")
    repository = root or pathlib.Path(__file__).resolve().parent.parent
    planned = _planned_commands(options)
    record: dict[str, Any] = {
        "schema": 1,
        "status": "dry-run",
        "source": options.source,
        "ref": options.ref,
        "hosts": list(_hosts(options.host)),
        "planned_commands": planned,
        "created": {"marketplaces": [], "plugins": []},
    }
    if not options.execute:
        return record

    options.state_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    transaction_path = options.state_dir / f"install-{stamp}-{uuid.uuid4().hex[:8]}.json"
    record["transaction_path"] = str(transaction_path)
    record["started_at"] = datetime.now(UTC).isoformat()
    record["before"] = {}
    record["status"] = "in-progress"
    record["pending"] = None
    _persist_record(transaction_path, record)

    try:
        for host in _hosts(options.host):
            before_marketplaces = _marketplaces(host, runner)
            before_plugins = _plugins(host, runner)
            record["before"][host] = {
                "marketplaces": sorted(before_marketplaces),
                "plugins": sorted(before_plugins),
            }
            _persist_record(transaction_path, record)
            if "divan" in before_marketplaces:
                raise InstallError(
                    f"{host}: existing divan marketplace source/ref cannot be proven; "
                    "no existing entry was changed"
                )
            orphaned_divan_plugins = sorted(
                plugin for plugin in before_plugins if plugin.endswith("@divan")
            )
            if orphaned_divan_plugins:
                raise InstallError(
                    f"{host}: existing divan plugin source/ref cannot be proven: "
                    f"{', '.join(orphaned_divan_plugins)}; no existing entry was changed"
                )
            _begin_mutation(
                transaction_path,
                record,
                {"kind": "marketplace", "host": host},
            )
            _run(runner, _add_marketplace_command(host, options.source, options.ref))
            record["created"]["marketplaces"].append(host)
            _finish_mutation(transaction_path, record)
            for package in PACKAGES:
                selector = f"{package}@divan"
                if selector in before_plugins:
                    continue
                _begin_mutation(
                    transaction_path,
                    record,
                    {"kind": "plugin", "host": host, "id": selector},
                )
                _run(runner, _install_command(host, package))
                record["created"]["plugins"].append({"host": host, "id": selector})
                _finish_mutation(transaction_path, record)

            installed = _plugins(host, runner)
            missing = [f"{package}@divan" for package in PACKAGES if f"{package}@divan" not in installed]
            if missing:
                raise InstallError(f"{host} verification failed; missing: {', '.join(missing)}")

        record["status"] = "verified"
        if options.migrate_legacy:
            _begin_mutation(
                transaction_path,
                record,
                {"kind": "legacy-migration", "host": "codex"},
            )
            record["legacy_migration_command"] = _migrate_legacy(repository, runner)
            _finish_mutation(transaction_path, record)
        record["finished_at"] = datetime.now(UTC).isoformat()
        _persist_record(transaction_path, record)
        return record
    except BaseException as exc:
        rollback_errors: list[str] = []
        pending = record.get("pending")
        rollback_plugins = list(record["created"]["plugins"])
        rollback_marketplaces = list(record["created"]["marketplaces"])
        if isinstance(pending, dict) and pending.get("kind") == "plugin":
            pending_host, pending_id = pending.get("host"), pending.get("id")
            candidate = {"host": pending_host, "id": pending_id}
            if (
                pending_host in {"claude", "codex"}
                and isinstance(pending_id, str)
                and candidate not in rollback_plugins
            ):
                rollback_plugins.append(candidate)
        elif isinstance(pending, dict) and pending.get("kind") == "marketplace":
            pending_host = pending.get("host")
            if pending_host in {"claude", "codex"} and pending_host not in rollback_marketplaces:
                rollback_marketplaces.append(pending_host)
        for plugin in reversed(rollback_plugins):
            try:
                if plugin["id"] in _plugins(plugin["host"], runner):
                    _begin_mutation(
                        transaction_path,
                        record,
                        {"kind": "rollback-plugin", **plugin},
                    )
                    _run(runner, _remove_plugin_command(plugin["host"], plugin["id"]))
                    _finish_mutation(transaction_path, record)
            except InstallError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        for host in reversed(rollback_marketplaces):
            try:
                if "divan" in _marketplaces(host, runner):
                    _begin_mutation(
                        transaction_path,
                        record,
                        {"kind": "rollback-marketplace", "host": host},
                    )
                    _run(runner, _remove_marketplace_command(host))
                    _finish_mutation(transaction_path, record)
            except InstallError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        record["status"] = "rolled-back" if not rollback_errors else "rollback-incomplete"
        record["error"] = str(exc)
        record["rollback_errors"] = rollback_errors
        record["pending"] = None
        record["finished_at"] = datetime.now(UTC).isoformat()
        _persist_record(transaction_path, record)
        raise InstallError(f"{exc}; transaction: {transaction_path}") from exc


def _parse_options(argv: list[str] | None = None) -> Options:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--source", default="trugurpala/divan")
    parser.add_argument("--ref", required=True, help="immutable release tag or commit")
    parser.add_argument("--execute", action="store_true", help="apply the printed plan")
    parser.add_argument("--migrate-legacy", action="store_true")
    parser.add_argument(
        "--state-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".divan" / "transactions",
    )
    parsed = parser.parse_args(argv)
    if parsed.migrate_legacy and not parsed.execute:
        parser.error("--migrate-legacy requires --execute")
    if parsed.migrate_legacy and parsed.host == "claude":
        parser.error("--migrate-legacy requires --host codex or --host both")
    return Options(
        host=parsed.host,
        source=parsed.source,
        ref=parsed.ref,
        execute=parsed.execute,
        migrate_legacy=parsed.migrate_legacy,
        state_dir=parsed.state_dir,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--rollback-transaction" in arguments:
        parser = argparse.ArgumentParser(description="Recover an interrupted Divan install")
        parser.add_argument("--rollback-transaction", type=pathlib.Path, required=True)
        recovery = parser.parse_args(arguments)
        try:
            record = rollback_transaction(recovery.rollback_transaction)
        except InstallError as exc:
            print(f"HATA: {exc}", file=sys.stderr)
            return 1
        print(f"RECOVERED - transaction: {record['transaction_path']}")
        return 0
    options = _parse_options(arguments)
    try:
        record = install(options)
    except InstallError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    if record["status"] == "dry-run":
        print("DRY-RUN - no host state changed. Add --execute to apply:")
        for command in record["planned_commands"]:
            print("  " + subprocess.list2cmdline(command))
    else:
        print(f"VERIFIED - transaction: {record['transaction_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
