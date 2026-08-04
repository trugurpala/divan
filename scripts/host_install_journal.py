"""Fingerprint authority and recovery for schema-1 native host installs."""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime
from typing import Any

import host_adapters
import host_install_authority
import host_install_marketplace
import host_state
import host_transactions
from host_install_marketplace import (
    InstallIO,
    InstallJournalError,
    capture_marketplace,
)

marketplace_confirmation = host_install_marketplace.marketplace_confirmation


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
    path: pathlib.Path,
    record: dict[str, Any],
    io: InstallIO,
    confirmation: str | None = None,
) -> dict[str, Any]:
    validate(record, path)
    _promote_forward(path, record, io, confirmation)
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
        if capture_marketplace(record, entry["host"], io, current) != entry:
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
    path: pathlib.Path,
    record: dict[str, Any],
    io: InstallIO,
    confirmation: str | None,
) -> None:
    pending = record.get("pending")
    if not isinstance(pending, dict):
        return
    if (
        pending.get("phase") == "recovery"
        and pending.get("action") == "remove-marketplace"
    ):
        host_install_marketplace.resume_pending_removal(path, record, pending, io)
        return
    action = pending.get("action")
    if action == "add-marketplace":
        if not host_install_marketplace.promote_pending(
            path, record, pending["host"], io, confirmation
        ):
            return
    elif action == "install-plugin":
        _promote_pending_plugin(record, pending["host"], pending["id"], io)
    else:
        return
    record["pending"] = None
    host_transactions.persist_record(path, record)


def _promote_pending_plugin(
    record: dict[str, Any], host: str, selector: str, io: InstallIO
) -> None:
    if selector in io.plugin_rows(host):
        _append_unique(
            record["created"]["plugins"], capture_plugin(record, host, selector, io)
        )


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
