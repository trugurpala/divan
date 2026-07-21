"""Fingerprint authority and recovery for schema-1 native host installs."""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import host_adapters
import host_install_authority
import host_state
import host_transactions


class InstallJournalError(host_transactions.TransactionError):
    """Raised before an install journal can mutate an unproven host row."""


@dataclass(frozen=True)
class InstallIO:
    marketplace_rows: Callable[[str], dict[str, dict[str, Any]]]
    plugin_rows: Callable[[str], dict[str, dict[str, Any]]]
    run: Callable[[list[str]], str]
    normalize_source: Callable[[str], str]


def new_record(
    source: str, ref: str, hosts: tuple[str, ...], planned: list[list[str]]
) -> dict[str, Any]:
    return {
        "schema": 1,
        "operation": "install",
        "fingerprint_schema": 1,
        "status": "dry-run",
        "source": source,
        "ref": ref,
        "hosts": list(hosts),
        "planned_commands": planned,
        "created": {"marketplaces": [], "plugins": []},
        "verified": {},
    }


def intent(
    phase: str,
    action: str,
    host: str,
    *,
    selector: str | None = None,
    journal: str | None = None,
) -> dict[str, str]:
    value = {"phase": phase, "action": action, "host": host}
    if selector is not None:
        value["id"] = selector
    if journal is not None:
        value["journal"] = journal
    return value


def target_evidence(
    root: pathlib.Path,
    source: str,
    ref: str,
    versions: dict[str, str],
    io: InstallIO,
) -> dict[str, Any]:
    try:
        evidence = host_state.checkout_evidence(
            root, source, ref, io.run, io.normalize_source
        )
    except host_state.StateError as exc:
        raise InstallJournalError(str(exc)) from exc
    if evidence["contract"] != versions:
        raise InstallJournalError("install target contract does not match native catalog")
    contract = evidence.pop("contract")
    return {**evidence, "versions": contract}


def capture_marketplace(
    record: dict[str, Any], host: str, io: InstallIO
) -> dict[str, Any]:
    row = io.marketplace_rows(host).get("divan")
    if row is None:
        raise InstallJournalError(f"{host}: created marketplace is missing")
    target = record["target"]
    try:
        evidence = host_state.marketplace_evidence(
            host,
            row,
            target["source"],
            target["ref"],
            io.run,
            io.normalize_source,
        )
    except host_state.StateError as exc:
        raise InstallJournalError(str(exc)) from exc
    if evidence["contract"] != target["versions"] or any(
        evidence[key] != target[key] for key in ("commit", "catalog_digest")
    ):
        raise InstallJournalError(f"{host}: created marketplace fingerprint is not target")
    return host_state.marketplace_fingerprint(host, evidence)


def capture_plugin(
    record: dict[str, Any], host: str, selector: str, io: InstallIO
) -> dict[str, Any]:
    marketplace = next(
        (row for row in record["created"]["marketplaces"] if row["host"] == host),
        None,
    )
    row = io.plugin_rows(host).get(selector)
    if marketplace is None or row is None:
        raise InstallJournalError(f"{host}: created {selector} ownership is missing")
    try:
        fingerprint = host_state.plugin_fingerprint(
            host,
            selector,
            row,
            pathlib.Path(marketplace["root"]),
            marketplace["source"],
        )
    except host_state.StateError as exc:
        raise InstallJournalError(str(exc)) from exc
    package = selector.removesuffix("@divan")
    if fingerprint["version"] != record["target"]["versions"][package]:
        raise InstallJournalError(f"{host}: created {selector} version is not target")
    return fingerprint


def validate(record: dict[str, Any], path: pathlib.Path | None = None) -> None:
    try:
        host_install_authority.validate(record, path)
    except host_install_authority.AuthorityError as exc:
        raise InstallJournalError(str(exc)) from exc


def recover_native(
    path: pathlib.Path, record: dict[str, Any], io: InstallIO
) -> dict[str, Any]:
    validate(record, path)
    _promote_forward(path, record, io)
    record["status"] = "recovering"
    host_transactions.persist_record(path, record)
    for entry in reversed(record["created"]["plugins"]):
        current = io.plugin_rows(entry["host"]).get(entry["id"])
        if current is None:
            continue
        try:
            fingerprint = host_state.plugin_fingerprint(
                entry["host"],
                entry["id"],
                current,
                pathlib.Path(entry["marketplace_root"]),
                record["target"]["source"],
            )
        except host_state.StateError as exc:
            raise InstallJournalError(str(exc)) from exc
        if fingerprint != entry:
            raise InstallJournalError(f"{entry['host']}: recovery refuses replaced {entry['id']}")
        _mutation(
            path,
            record,
            {"phase": "recovery", "action": "remove-plugin", "host": entry["host"], "id": entry["id"]},
            host_adapters.remove_plugin_command(entry["host"], entry["id"]),
            io,
        )
    for entry in reversed(record["created"]["marketplaces"]):
        current = io.marketplace_rows(entry["host"]).get("divan")
        if current is None:
            continue
        if capture_marketplace(record, entry["host"], io) != entry:
            raise InstallJournalError(
                f"{entry['host']}: recovery refuses replaced marketplace"
            )
        _mutation(
            path,
            record,
            {"phase": "recovery", "action": "remove-marketplace", "host": entry["host"]},
            host_adapters.remove_marketplace_command(entry["host"]),
            io,
        )
    record["status"] = "recovered"
    record["pending"] = None
    record["recovered_at"] = datetime.now(UTC).isoformat()
    host_transactions.persist_record(path, record)
    return record


def _promote_forward(
    path: pathlib.Path, record: dict[str, Any], io: InstallIO
) -> None:
    pending = record.get("pending")
    if not isinstance(pending, dict) or pending.get("action") not in {
        "add-marketplace", "install-plugin",
    }:
        return
    host = pending["host"]
    if pending["action"] == "add-marketplace":
        if "divan" in io.marketplace_rows(host):
            _append_unique(record["created"]["marketplaces"], capture_marketplace(record, host, io))
    elif pending["id"] in io.plugin_rows(host):
        _append_unique(
            record["created"]["plugins"], capture_plugin(record, host, pending["id"], io)
        )
    record["pending"] = None
    host_transactions.persist_record(path, record)


def _mutation(
    path: pathlib.Path,
    record: dict[str, Any],
    pending: dict[str, str],
    command: list[str],
    io: InstallIO,
) -> None:
    host_transactions.begin_mutation(path, record, pending)
    io.run(command)
    host_transactions.finish_mutation(path, record)


def _append_unique(rows: list[Any], entry: Any) -> None:
    if entry not in rows:
        rows.append(entry)
