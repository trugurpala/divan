"""Fingerprint authority and recovery for schema-1 native host installs."""

from __future__ import annotations

import pathlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import host_adapters
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
        "fingerprint_schema": 1,
        "status": "dry-run",
        "source": source,
        "ref": ref,
        "hosts": list(hosts),
        "planned_commands": planned,
        "created": {"marketplaces": [], "plugins": []},
        "verified": {},
    }


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
            host, selector, row, pathlib.Path(marketplace["root"])
        )
    except host_state.StateError as exc:
        raise InstallJournalError(str(exc)) from exc
    package = selector.removesuffix("@divan")
    if fingerprint["version"] != record["target"]["versions"][package]:
        raise InstallJournalError(f"{host}: created {selector} version is not target")
    return fingerprint


def validate(record: dict[str, Any]) -> None:
    if record.get("fingerprint_schema") != 1:
        raise InstallJournalError("legacy install journal lacks exact fingerprints")
    target, created, before = record.get("target"), record.get("created"), record.get("before")
    if (
        not isinstance(target, dict)
        or not _target(target)
        or not isinstance(created, dict)
        or not isinstance(before, dict)
    ):
        raise InstallJournalError("install journal fingerprint authority is malformed")
    markets, plugins = created.get("marketplaces"), created.get("plugins")
    if not isinstance(markets, list) or not isinstance(plugins, list):
        raise InstallJournalError("install journal created fingerprints are malformed")
    if not _created_marketplaces(markets, target, before):
        raise InstallJournalError("install marketplace fingerprints are invalid")
    if not _created_plugins(plugins, markets, target, before):
        raise InstallJournalError("install plugin fingerprints are invalid")


def recover_native(
    path: pathlib.Path, record: dict[str, Any], io: InstallIO
) -> dict[str, Any]:
    validate(record)
    _promote_forward(path, record, io)
    record["status"] = "recovering"
    host_transactions.persist_record(path, record)
    for entry in reversed(record["created"]["plugins"]):
        current = io.plugin_rows(entry["host"]).get(entry["id"])
        if current is None:
            continue
        try:
            fingerprint = host_state.plugin_fingerprint(
                entry["host"], entry["id"], current, pathlib.Path(entry["marketplace_root"])
            )
        except host_state.StateError as exc:
            raise InstallJournalError(str(exc)) from exc
        if fingerprint != entry:
            raise InstallJournalError(f"{entry['host']}: recovery refuses replaced {entry['id']}")
        _mutation(
            path,
            record,
            {"kind": "recovery-plugin", "host": entry["host"], "id": entry["id"]},
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
            {"kind": "recovery-marketplace", "host": entry["host"]},
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
    if not isinstance(pending, dict) or pending.get("kind") not in {"marketplace", "plugin"}:
        return
    host = pending["host"]
    if pending["kind"] == "marketplace":
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


def _target(value: Any) -> bool:
    expected = {"source", "ref", "root", "commit", "catalog_digest", "versions"}
    return bool(
        isinstance(value, dict)
        and set(value) == expected
        and all(isinstance(value[key], str) and value[key] for key in expected - {"versions"})
        and re.fullmatch(r"[0-9a-f]{40}", value["commit"])
        and re.fullmatch(r"[0-9a-f]{64}", value["catalog_digest"])
        and isinstance(value["versions"], dict)
        and set(value["versions"]) == set(host_state.PACKAGES)
        and all(isinstance(item, str) and item for item in value["versions"].values())
    )


def _created_marketplaces(
    rows: list[Any], target: dict[str, Any], before: dict[str, Any]
) -> bool:
    expected = {"host", "source", "ref", "root", "commit", "catalog_digest"}
    keys: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected or row["host"] not in before:
            return False
        if "divan" in before[row["host"]].get("marketplaces", []):
            return False
        if any(row[key] != target[key] for key in ("source", "ref", "commit", "catalog_digest")):
            return False
        keys.append(row["host"])
    return len(keys) == len(set(keys))


def _created_plugins(
    rows: list[Any], markets: list[Any], target: dict[str, Any], before: dict[str, Any]
) -> bool:
    expected = {
        "host", "id", "version", "marketplace_root", "install_path", "native_provenance",
    }
    roots = {row["host"]: row["root"] for row in markets}
    keys: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected or row["host"] not in roots:
            return False
        selector = row["id"]
        if not isinstance(selector, str) or not selector.endswith("@divan"):
            return False
        package = selector.removesuffix("@divan")
        if package not in target["versions"] or row["version"] != target["versions"][package]:
            return False
        if selector in before[row["host"]].get("plugins", []):
            return False
        if row["native_provenance"] is not True or row["marketplace_root"] != roots[row["host"]]:
            return False
        if host_adapters.native_install_path(
            row["host"], row["install_path"], pathlib.Path(roots[row["host"]]), package, row["version"]
        ) is None:
            return False
        keys.append((row["host"], selector))
    return len(keys) == len(set(keys))


def _append_unique(rows: list[Any], entry: Any) -> None:
    if entry not in rows:
        rows.append(entry)
