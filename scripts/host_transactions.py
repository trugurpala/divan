"""Versioned, host-neutral transaction journal primitives for Divan."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import host_adapters
import host_journal
import host_state


class TransactionError(RuntimeError):
    """Raised when a transaction journal cannot be trusted or recovered."""


def persist_record(path: pathlib.Path, record: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def begin_mutation(path: pathlib.Path, record: dict[str, Any], pending: dict[str, str]) -> None:
    record["pending"] = pending
    persist_record(path, record)


def finish_mutation(path: pathlib.Path, record: dict[str, Any]) -> None:
    record["pending"] = None
    persist_record(path, record)


def load_transaction(path: pathlib.Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError(f"transaction journal is unreadable: {path}") from exc
    if not isinstance(record, dict) or record.get("schema") not in {1, 2}:
        raise TransactionError("unsupported transaction journal schema")
    return record


def load_recoverable_transaction(
    path: pathlib.Path, normalize_source: Callable[[str], str] | None = None
) -> dict[str, Any]:
    record = load_transaction(path)
    if record.get("status") not in {
        "in-progress",
        "rollback-incomplete",
        "recovering",
        "verified",
    }:
        raise TransactionError(f"transaction is not recoverable: {record.get('status')}")
    upgrade = record["schema"] == 2 or record.get("operation") == "upgrade"
    if upgrade or path.name.startswith("upgrade-"):
        if normalize_source is None:
            raise TransactionError("schema-2 recovery requires source normalization")
        try:
            host_journal.validate_schema2(path, record, normalize_source)
        except host_journal.JournalError as exc:
            raise TransactionError(str(exc)) from exc
    ownership = "before" if record["schema"] == 1 else "before_rows"
    if not isinstance(record.get(ownership), dict) or not isinstance(
        record.get("created"), dict
    ):
        raise TransactionError("transaction journal lacks ownership state")
    return record


def schema1_created_rows(record: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    created = record["created"]
    plugin_rows = list(created.get("plugins", []))
    marketplace_hosts = list(created.get("marketplaces", []))
    pending = record.get("pending")
    if isinstance(pending, dict) and pending.get("kind") in {
        "plugin",
        "rollback-plugin",
        "recovery-plugin",
    }:
        plugin_rows.append({"host": pending.get("host"), "id": pending.get("id")})
    elif isinstance(pending, dict) and pending.get("kind") in {
        "marketplace",
        "rollback-marketplace",
        "recovery-marketplace",
    }:
        marketplace_hosts.append(pending.get("host"))
    return plugin_rows, marketplace_hosts


def schema1_owned_plugins(plugin_rows: list[Any], before: dict[str, Any]) -> list[dict[str, str]]:
    owned: list[dict[str, str]] = []
    for row in plugin_rows:
        if not isinstance(row, dict):
            raise TransactionError("transaction contains an invalid plugin entry")
        host, selector = row.get("host"), row.get("id")
        if host not in {"claude", "codex"} or not isinstance(selector, str):
            raise TransactionError("transaction contains an invalid plugin identity")
        if not selector.endswith("@divan"):
            raise TransactionError("transaction refuses to remove a non-Divan plugin")
        if selector in before.get(host, {}).get("plugins", []):
            raise TransactionError(f"transaction does not own pre-existing plugin: {selector}")
        if row not in owned:
            owned.append({"host": host, "id": selector})
    return owned


def schema1_owned_marketplaces(marketplace_hosts: list[Any], before: dict[str, Any]) -> list[str]:
    owned: list[str] = []
    for host in marketplace_hosts:
        if host not in {"claude", "codex"}:
            raise TransactionError("transaction contains an invalid marketplace host")
        if "divan" in before.get(host, {}).get("marketplaces", []):
            raise TransactionError(f"transaction does not own pre-existing marketplace: {host}")
        if host not in owned:
            owned.append(host)
    return owned


def recovery_command(path: pathlib.Path) -> str:
    script = pathlib.Path(__file__).resolve().with_name("divan.py")
    return subprocess.list2cmdline(
        [sys.executable, str(script), "recover", str(path.resolve())]
    )


@dataclass(frozen=True)
class RecoveryIO:
    marketplace_rows: Callable[[str], dict[str, dict[str, Any]]]
    plugin_rows: Callable[[str], dict[str, dict[str, Any]]]
    normalize_source: Callable[[str], str]
    run: Callable[[list[str]], str]


def mark_rollback_incomplete(path: pathlib.Path, record: dict[str, Any], error: BaseException) -> None:
    detail = str(error) or type(error).__name__
    record["status"] = "rollback-incomplete"
    record.setdefault("rollback_errors", []).append(detail)
    record["recovery_command"] = recovery_command(path)
    persist_record(path, record)


def _recovery_mutation(
    path: pathlib.Path,
    record: dict[str, Any],
    pending: dict[str, str],
    command: list[str],
    io: RecoveryIO,
) -> None:
    record["recovery_pending"] = pending
    persist_record(path, record)
    io.run(command)
    record["recovery_pending"] = None
    persist_record(path, record)


def _marketplace_evidence(
    host: str, row: dict[str, Any], expected: dict[str, Any], io: RecoveryIO
) -> dict[str, Any]:
    try:
        return host_state.marketplace_evidence(
            host, row, expected["source"], expected["ref"], io.run, io.normalize_source
        )
    except host_state.StateError as exc:
        raise TransactionError(str(exc)) from exc


def _marketplace_fingerprint(
    host: str, row: dict[str, Any], expected: dict[str, Any], io: RecoveryIO
) -> dict[str, Any]:
    return host_state.marketplace_fingerprint(
        host, _marketplace_evidence(host, row, expected, io)
    )


def _plugin_fingerprint(
    host: str, selector: str, row: dict[str, Any], root: str, source: str
) -> dict[str, Any]:
    try:
        return host_state.plugin_fingerprint(host, selector, row, pathlib.Path(root), source)
    except host_state.StateError as exc:
        raise TransactionError(str(exc)) from exc


def _append_unique(rows: list[Any], entry: Any) -> None:
    if entry not in rows:
        rows.append(entry)


def _promote_forward(path: pathlib.Path, record: dict[str, Any], io: RecoveryIO) -> None:
    pending = record.get("pending")
    if not isinstance(pending, dict):
        return
    host, action = pending["host"], pending["action"]
    markets, plugins = io.marketplace_rows(host), io.plugin_rows(host)
    if action == "add-marketplace" and "divan" in markets:
        entry = _marketplace_fingerprint(host, markets["divan"], record["target"], io)
        _append_unique(record["created"]["marketplaces"], entry)
    elif action == "install-plugin" and pending["id"] in plugins:
        target_market = next((row for row in record["created"]["marketplaces"] if row["host"] == host), None)
        if target_market is None:
            raise TransactionError(f"{host}: target marketplace ownership is missing")
        entry = _plugin_fingerprint(host, pending["id"], plugins[pending["id"]], target_market["root"], target_market["source"])
        _append_unique(record["created"]["plugins"], entry)
    elif action == "remove-plugin" and pending["id"] not in plugins:
        _append_unique(record["removed"], {"kind": "plugin", "host": host, "id": pending["id"]})
    elif action == "remove-marketplace" and "divan" not in markets:
        _append_unique(record["removed"], {"kind": "marketplace", "host": host})
    record["pending"] = None
    persist_record(path, record)


def _remove_target_plugins(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: RecoveryIO,
) -> None:
    installed = io.plugin_rows(host)
    entries = [row for row in record["created"]["plugins"] if row["host"] == host]
    source = record["target"]["source"]
    for entry in reversed(entries):
        selector = entry["id"]
        if selector not in installed:
            continue
        current = _plugin_fingerprint(
            host, selector, installed[selector], entry["marketplace_root"], source
        )
        if current != entry:
            raise TransactionError(f"{host}: recovery refuses replaced {selector}")
        _recovery_mutation(
            path,
            record,
            {"phase": "recovery", "action": "remove-target-plugin", "host": host, "id": selector},
            host_adapters.remove_plugin_command(host, selector),
            io,
        )


def _cleanup_target_host(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: RecoveryIO,
) -> None:
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is None:
        return
    before = host_state.marketplace_fingerprint(host, record["before_rows"][host])
    try:
        if _marketplace_fingerprint(host, marketplace, record["before_rows"][host], io) == before:
            return
    except TransactionError:
        pass
    created = next(
        (row for row in record["created"]["marketplaces"] if row["host"] == host), None
    )
    if created is None:
        raise TransactionError(f"{host}: transaction does not own target marketplace")
    current = _marketplace_fingerprint(host, marketplace, record["target"], io)
    if current != created:
        raise TransactionError(f"{host}: recovery refuses replaced marketplace")
    _remove_target_plugins(path, record, host, io)
    _recovery_mutation(
        path,
        record,
        {"phase": "recovery", "action": "remove-target-marketplace", "host": host},
        host_adapters.remove_marketplace_command(host),
        io,
    )


def _restore_marketplace(
    path: pathlib.Path, record: dict[str, Any], host: str, io: RecoveryIO
) -> None:
    before = record["before_rows"][host]
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is not None:
        _require_exact_marketplace(host, marketplace, before, io)
        _clear_restore_intent(path, record, host)
        return
    record["recovery_pending"] = {
        "phase": "recovery",
        "action": "restore-marketplace",
        "host": host,
    }
    persist_record(path, record)
    io.run(host_adapters.add_marketplace_command(host, before["source"], before["ref"]))
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is None:
        raise TransactionError(f"{host}: restored marketplace is missing")
    _require_exact_marketplace(host, marketplace, before, io)
    record["recovery_pending"] = None
    persist_record(path, record)


def _require_exact_marketplace(
    host: str, marketplace: dict[str, Any], before: dict[str, Any], io: RecoveryIO
) -> None:
    current = _marketplace_fingerprint(host, marketplace, before, io)
    if current != host_state.marketplace_fingerprint(host, before):
        raise TransactionError(f"{host}: recovery found a conflicting marketplace")


def _clear_restore_intent(path: pathlib.Path, record: dict[str, Any], host: str) -> None:
    pending = record.get("recovery_pending")
    if not isinstance(pending, dict) or pending.get("action") != "restore-marketplace":
        return
    if pending.get("host") != host:
        return
    record["recovery_pending"] = None
    persist_record(path, record)


def _restore_plugins(
    path: pathlib.Path, record: dict[str, Any], host: str, io: RecoveryIO
) -> None:
    before = record["before_rows"][host]
    installed = io.plugin_rows(host)
    root, source = before["root"], before["source"]
    for selector, before_row in before["plugins"].items():
        current = installed.get(selector)
        if current is not None:
            expected = _plugin_fingerprint(host, selector, before_row, root, source)
            actual = _plugin_fingerprint(host, selector, current, root, source)
            if actual != expected:
                raise TransactionError(f"{host}: recovery found conflicting {selector}")
            continue
        package = selector.removesuffix("@divan")
        _recovery_mutation(
            path,
            record,
            {"phase": "recovery", "action": "restore-plugin", "host": host, "id": selector},
            host_adapters.install_command(host, package),
            io,
        )
        installed = io.plugin_rows(host)


def _verify_restored(record: dict[str, Any], host: str, io: RecoveryIO) -> None:
    before = record["before_rows"][host]
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is None:
        raise TransactionError(f"{host}: prior marketplace was not restored")
    current = _marketplace_fingerprint(host, marketplace, before, io)
    if current != host_state.marketplace_fingerprint(host, before):
        raise TransactionError(f"{host}: prior marketplace was not restored exactly")
    try:
        host_state.validate_plugins(
            host, pathlib.Path(before["root"]), before["contract"], io.plugin_rows(host)
        )
    except host_state.StateError as exc:
        raise TransactionError(str(exc)) from exc


def _affected_hosts(record: dict[str, Any]) -> set[str]:
    hosts = {row["host"] for row in record["removed"]}
    hosts.update(row["host"] for row in record["created"]["plugins"])
    hosts.update(row["host"] for row in record["created"]["marketplaces"])
    recovery = record.get("recovery_pending")
    if isinstance(recovery, dict):
        hosts.add(recovery["host"])
    return hosts


def recover_upgrade(
    path: pathlib.Path, record: dict[str, Any], io: RecoveryIO
) -> dict[str, Any]:
    hosts = list(record.get("hosts", []))
    try:
        _promote_forward(path, record, io)
        affected = _affected_hosts(record)
        record["status"] = "recovering"
        persist_record(path, record)
        for host in reversed(hosts):
            if host in affected:
                _cleanup_target_host(path, record, host, io)
        for host in reversed(hosts):
            if host in affected:
                _restore_marketplace(path, record, host, io)
                _restore_plugins(path, record, host, io)
                _verify_restored(record, host, io)
    except BaseException as exc:
        mark_rollback_incomplete(path, record, exc)
        raise
    record["status"] = "recovered"
    record["pending"] = None
    record["recovery_pending"] = None
    record["rollback_errors"] = []
    persist_record(path, record)
    return record
