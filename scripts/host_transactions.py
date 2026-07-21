"""Versioned, host-neutral transaction journal primitives for Divan."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import host_adapters


class TransactionError(RuntimeError):
    """Raised when a transaction journal cannot be trusted or recovered."""


def persist_record(path: pathlib.Path, record: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def begin_mutation(
    path: pathlib.Path, record: dict[str, Any], pending: dict[str, str]
) -> None:
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


def load_recoverable_transaction(path: pathlib.Path) -> dict[str, Any]:
    record = load_transaction(path)
    if record.get("status") not in {
        "in-progress",
        "rollback-incomplete",
        "recovering",
        "verified",
    }:
        raise TransactionError(f"transaction is not recoverable: {record.get('status')}")
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


def schema1_owned_plugins(
    plugin_rows: list[Any], before: dict[str, Any]
) -> list[dict[str, str]]:
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


def schema1_owned_marketplaces(
    marketplace_hosts: list[Any], before: dict[str, Any]
) -> list[str]:
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
    return subprocess.list2cmdline(
        ["python", "scripts/kur-hostlar.py", "--rollback-transaction", str(path)]
    )


@dataclass(frozen=True)
class RecoveryIO:
    marketplace_rows: Callable[[str], dict[str, dict[str, Any]]]
    plugin_rows: Callable[[str], dict[str, dict[str, Any]]]
    marketplace_identity: Callable[[str, dict[str, Any]], tuple[str, str]]
    normalize_source: Callable[[str], str]
    run: Callable[[list[str]], str]


def mark_rollback_incomplete(
    path: pathlib.Path, record: dict[str, Any], error: BaseException
) -> None:
    detail = str(error) or type(error).__name__
    record["status"] = "rollback-incomplete"
    record.setdefault("rollback_errors", []).append(detail)
    record["recovery_command"] = recovery_command(path)
    persist_record(path, record)


def _mutation(
    path: pathlib.Path,
    record: dict[str, Any],
    pending: dict[str, str],
    command: list[str],
    io: RecoveryIO,
) -> None:
    begin_mutation(path, record, pending)
    io.run(command)
    finish_mutation(path, record)


def _snapshot_identity(snapshot: dict[str, Any]) -> tuple[str, str]:
    source, ref = snapshot.get("source"), snapshot.get("ref")
    if not isinstance(source, str) or not isinstance(ref, str):
        raise TransactionError("upgrade journal lacks proven marketplace identity")
    return source, ref


def _same_identity(
    io: RecoveryIO, left: tuple[str, str], right: tuple[str, str]
) -> bool:
    return io.normalize_source(left[0]) == io.normalize_source(right[0]) and left[1] == right[1]


def _created_plugin_ids(record: dict[str, Any], host: str) -> list[str]:
    rows = record["created"].get("plugins", [])
    selectors = [
        row.get("id")
        for row in rows
        if isinstance(row, dict) and row.get("host") == host
    ]
    pending = record.get("pending")
    if (
        isinstance(pending, dict)
        and pending.get("phase") == "forward"
        and pending.get("action") == "install-plugin"
        and pending.get("host") == host
    ):
        selectors.append(pending.get("id"))
    return list(dict.fromkeys(item for item in selectors if isinstance(item, str)))


def _created_marketplace(record: dict[str, Any], host: str) -> bool:
    if host in record["created"].get("marketplaces", []):
        return True
    pending = record.get("pending")
    return bool(
        isinstance(pending, dict)
        and pending.get("phase") == "forward"
        and pending.get("action") == "add-marketplace"
        and pending.get("host") == host
    )


def _remove_target_plugins(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: RecoveryIO,
) -> None:
    installed = io.plugin_rows(host)
    for selector in reversed(_created_plugin_ids(record, host)):
        if selector not in installed:
            continue
        _mutation(
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
    identity = io.marketplace_identity(host, marketplace)
    if _same_identity(io, identity, _snapshot_identity(record["before_rows"][host])):
        return
    target = record["target"]
    target_identity = (target.get("source"), target.get("ref"))
    if not all(isinstance(item, str) for item in target_identity) or not _same_identity(
        io, identity, target_identity
    ):
        raise TransactionError(f"{host}: recovery refuses an unknown marketplace identity")
    _remove_target_plugins(path, record, host, io)
    if not _created_marketplace(record, host):
        raise TransactionError(f"{host}: transaction does not own target marketplace")
    _mutation(
        path,
        record,
        {"phase": "recovery", "action": "remove-target-marketplace", "host": host},
        host_adapters.remove_marketplace_command(host),
        io,
    )


def _plugin_matches(host: str, row: dict[str, Any], before: dict[str, Any]) -> bool:
    return bool(
        row.get("version") == before.get("version")
        and row.get("enabled") is True
        and host_adapters.plugin_provenance_valid(host, row)
    )


def _restore_marketplace(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: RecoveryIO,
) -> None:
    before = record["before_rows"][host]
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is not None:
        if not _same_identity(
            io, io.marketplace_identity(host, marketplace), _snapshot_identity(before)
        ):
            raise TransactionError(f"{host}: recovery found a conflicting marketplace")
        return
    source, ref = _snapshot_identity(before)
    _mutation(
        path,
        record,
        {"phase": "recovery", "action": "restore-marketplace", "host": host},
        host_adapters.add_marketplace_command(host, source, ref),
        io,
    )


def _restore_plugins(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: RecoveryIO,
) -> None:
    before_plugins = record["before_rows"][host]["plugins"]
    installed = io.plugin_rows(host)
    for selector, before in before_plugins.items():
        current = installed.get(selector)
        if current is not None:
            if not _plugin_matches(host, current, before):
                raise TransactionError(f"{host}: recovery found conflicting {selector}")
            continue
        package = selector.removesuffix("@divan")
        _mutation(
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
    if marketplace is None or not _same_identity(
        io, io.marketplace_identity(host, marketplace), _snapshot_identity(before)
    ):
        raise TransactionError(f"{host}: prior marketplace was not restored")
    installed = io.plugin_rows(host)
    for selector, expected in before["plugins"].items():
        if not _plugin_matches(host, installed.get(selector, {}), expected):
            raise TransactionError(f"{host}: prior {selector} was not restored")


def recover_upgrade(
    path: pathlib.Path, record: dict[str, Any], io: RecoveryIO
) -> dict[str, Any]:
    hosts = list(record.get("hosts", []))
    try:
        record["status"] = "recovering"
        persist_record(path, record)
        for host in reversed(hosts):
            _cleanup_target_host(path, record, host, io)
        for host in reversed(hosts):
            _restore_marketplace(path, record, host, io)
            _restore_plugins(path, record, host, io)
            _verify_restored(record, host, io)
    except BaseException as exc:
        mark_rollback_incomplete(path, record, exc)
        raise
    record["status"] = "recovered"
    record["pending"] = None
    record["rollback_errors"] = []
    persist_record(path, record)
    return record
