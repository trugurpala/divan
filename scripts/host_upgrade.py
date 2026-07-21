"""Provenance proof and forward orchestration for Divan host upgrades."""

from __future__ import annotations

import pathlib
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import host_adapters
import host_journal
import host_state
import host_transactions


@dataclass(frozen=True)
class UpgradeIO:
    marketplace_rows: Callable[[str], dict[str, dict[str, Any]]]
    plugin_rows: Callable[[str], dict[str, dict[str, Any]]]
    run: Callable[[list[str]], str]
    rollback: Callable[[pathlib.Path], dict[str, Any]]
    normalize_source: Callable[[str], str]


def _planned_commands(options: Any, packages: tuple[str, ...]) -> list[list[str]]:
    commands: list[list[str]] = []
    for host in options.hosts:
        commands.extend(
            host_adapters.remove_plugin_command(host, f"{package}@divan")
            for package in packages
        )
        commands.append(host_adapters.remove_marketplace_command(host))
        commands.append(
            host_adapters.add_marketplace_command(host, options.source, options.ref)
        )
        commands.extend(host_adapters.install_command(host, package) for package in packages)
    return commands


def _record(
    options: Any, packages: tuple[str, ...], versions: dict[str, str]
) -> dict[str, Any]:
    return {
        "schema": 2,
        "operation": "upgrade",
        "status": "dry-run",
        "source": options.source,
        "ref": options.ref,
        "hosts": list(options.hosts),
        "planned_commands": _planned_commands(options, packages),
        "before_rows": {},
        "target": {"source": options.source, "ref": options.ref, "versions": versions},
        "pending": None,
        "recovery_pending": None,
        "removed": [],
        "created": {"marketplaces": [], "plugins": []},
        "verified": {},
        "rollback_errors": [],
    }


def _mutation(
    path: pathlib.Path,
    record: dict[str, Any],
    pending: dict[str, str],
    command: list[str],
    completed: list[Any],
    entry: Any,
    io: UpgradeIO,
) -> None:
    host_transactions.begin_mutation(path, record, pending)
    io.run(command)
    completed.append(entry)
    host_transactions.finish_mutation(path, record)


def _remove_previous(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    packages: tuple[str, ...],
    io: UpgradeIO,
) -> None:
    for package in packages:
        selector = f"{package}@divan"
        entry = {"kind": "plugin", "host": host, "id": selector}
        pending = {
            "phase": "forward",
            "action": "remove-plugin",
            "host": host,
            "id": selector,
        }
        _mutation(
            path,
            record,
            pending,
            host_adapters.remove_plugin_command(host, selector),
            record["removed"],
            entry,
            io,
        )
    _remove_previous_marketplace(path, record, host, io)


def _remove_previous_marketplace(
    path: pathlib.Path, record: dict[str, Any], host: str, io: UpgradeIO
) -> None:
    _mutation(
        path,
        record,
        {"phase": "forward", "action": "remove-marketplace", "host": host},
        host_adapters.remove_marketplace_command(host),
        record["removed"],
        {"kind": "marketplace", "host": host},
        io,
    )


def _install_target(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    options: Any,
    packages: tuple[str, ...],
    io: UpgradeIO,
) -> None:
    pending = {"phase": "forward", "action": "add-marketplace", "host": host}
    host_transactions.begin_mutation(path, record, pending)
    io.run(host_adapters.add_marketplace_command(host, options.source, options.ref))
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is None:
        raise host_transactions.TransactionError(f"{host}: target marketplace is missing")
    try:
        evidence = host_state.marketplace_evidence(
            host,
            marketplace,
            record["target"]["source"],
            record["target"]["ref"],
            io.run,
            io.normalize_source,
        )
    except host_state.StateError as exc:
        raise host_transactions.TransactionError(str(exc)) from exc
    record["created"]["marketplaces"].append(
        host_state.marketplace_fingerprint(host, evidence)
    )
    host_transactions.finish_mutation(path, record)
    for package in packages:
        _install_target_plugin(path, record, host, package, io)


def _install_target_plugin(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    package: str,
    io: UpgradeIO,
) -> None:
    selector = f"{package}@divan"
    pending = {
        "phase": "forward",
        "action": "install-plugin",
        "host": host,
        "id": selector,
    }
    host_transactions.begin_mutation(path, record, pending)
    io.run(host_adapters.install_command(host, package))
    row = io.plugin_rows(host).get(selector)
    marketplace = next(
        entry for entry in record["created"]["marketplaces"] if entry["host"] == host
    )
    if row is None:
        raise host_transactions.TransactionError(f"{host}: installed {selector} is missing")
    try:
        fingerprint = host_state.plugin_fingerprint(
            host, selector, row, pathlib.Path(marketplace["root"])
        )
    except host_state.StateError as exc:
        raise host_transactions.TransactionError(str(exc)) from exc
    record["created"]["plugins"].append(fingerprint)
    host_transactions.finish_mutation(path, record)


def _matches_target(before: dict[str, Any], target: dict[str, Any], io: UpgradeIO) -> bool:
    return host_state.target_matches(before, target, io.normalize_source)


def _capture_host(host: str, source: str, ref: str, io: UpgradeIO) -> dict[str, Any]:
    try:
        return host_state.capture_host(
            host,
            source,
            ref,
            io.marketplace_rows(host),
            io.plugin_rows(host),
            io.run,
            io.normalize_source,
        )
    except host_state.StateError as exc:
        raise host_transactions.TransactionError(str(exc)) from exc


def _capture_before(host: str, source: str, io: UpgradeIO) -> dict[str, Any]:
    marketplaces = io.marketplace_rows(host)
    marketplace = marketplaces.get("divan")
    if marketplace is None:
        raise host_transactions.TransactionError(f"{host}: divan marketplace is missing")
    ref = host_adapters.marketplace_ref(marketplace)
    if ref is None:
        raise host_transactions.TransactionError(f"{host}: marketplace ref is missing")
    try:
        return host_state.capture_host(
            host,
            source,
            ref,
            marketplaces,
            io.plugin_rows(host),
            io.run,
            io.normalize_source,
        )
    except host_state.StateError as exc:
        raise host_transactions.TransactionError(str(exc)) from exc


def _assert_unchanged(host: str, expected: dict[str, Any], io: UpgradeIO) -> None:
    current = _capture_host(host, expected["source"], expected["ref"], io)
    if host_state.snapshot_key(host, current, io.normalize_source) != host_state.snapshot_key(
        host, expected, io.normalize_source
    ):
        raise host_transactions.TransactionError(f"{host}: host state drifted after preflight")


def _verify_target(host: str, record: dict[str, Any], io: UpgradeIO) -> dict[str, Any]:
    current = _capture_host(host, record["target"]["source"], record["target"]["ref"], io)
    if not _matches_target(current, record["target"], io):
        raise host_transactions.TransactionError(f"{host}: target fingerprint verification failed")
    return current


def _apply_host(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    options: Any,
    packages: tuple[str, ...],
    io: UpgradeIO,
) -> None:
    if not _matches_target(record["before_rows"][host], record["target"], io):
        _assert_unchanged(host, record["before_rows"][host], io)
        _remove_previous(path, record, host, packages, io)
        _install_target(path, record, host, options, packages, io)
    record["verified"][host] = _verify_target(host, record, io)
    host_transactions.persist_record(path, record)


def _fail(
    path: pathlib.Path, error: BaseException, io: UpgradeIO
) -> None:
    try:
        recovered = io.rollback(path)
    except BaseException as rollback_error:
        command = host_transactions.recovery_command(path)
        raise host_transactions.TransactionError(
            f"{error}; rollback incomplete: {rollback_error}; recovery: {command}"
        ) from error
    recovered["status"] = "rolled-back"
    recovered["error"] = str(error) or type(error).__name__
    recovered["finished_at"] = datetime.now(UTC).isoformat()
    host_transactions.persist_record(path, recovered)
    raise host_transactions.TransactionError(f"{error}; transaction: {path}") from error


def upgrade(
    options: Any,
    packages: tuple[str, ...],
    expected: dict[str, dict[str, Any]],
    io: UpgradeIO,
    repository: pathlib.Path,
) -> dict[str, Any]:
    versions = {package: row["version"] for package, row in expected.items()}
    record = _record(options, packages, versions)
    if not options.execute:
        return record
    try:
        with host_journal.UpgradeLock(options.state_dir):
            host_journal.assert_no_active(options.state_dir, io.normalize_source)
            return _execute(options, packages, versions, io, repository, record)
    except (host_journal.JournalError, host_state.StateError) as exc:
        raise host_transactions.TransactionError(str(exc)) from exc


def _execute(
    options: Any,
    packages: tuple[str, ...],
    versions: dict[str, str],
    io: UpgradeIO,
    repository: pathlib.Path,
    record: dict[str, Any],
) -> dict[str, Any]:
    target = host_state.checkout_evidence(
        repository, options.source, options.ref, io.run, io.normalize_source
    )
    if target["contract"] != versions:
        raise host_state.StateError("target checkout contract does not match native catalog")
    target_versions = target.pop("contract")
    record["target"] = {**target, "versions": target_versions}
    record["before_rows"] = {
        host: _capture_before(host, record["target"]["source"], io) for host in options.hosts
    }
    host_state.assert_consistent_snapshot_groups(record["before_rows"], io.normalize_source)
    for before in record["before_rows"].values():
        host_state.assert_same_ref_reproducible(before, record["target"], io.normalize_source)
    if all(_matches_target(before, record["target"], io) for before in record["before_rows"].values()):
        record["status"] = "no-op"
        return record
    options.state_dir.mkdir(parents=True, exist_ok=True)
    path = _start_transaction(options, record)
    try:
        for host in options.hosts:
            _apply_host(path, record, host, options, packages, io)
    except BaseException as exc:
        _fail(path, exc, io)
    record["status"] = "verified"
    record["finished_at"] = datetime.now(UTC).isoformat()
    host_transactions.persist_record(path, record)
    return record


def _start_transaction(options: Any, record: dict[str, Any]) -> pathlib.Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = (options.state_dir / f"upgrade-{stamp}-{uuid.uuid4().hex[:8]}.json").resolve()
    record.update(
        {
            "transaction_path": str(path),
            "recovery_command": host_transactions.recovery_command(path),
            "started_at": datetime.now(UTC).isoformat(),
            "status": "in-progress",
        }
    )
    host_transactions.persist_record(path, record)
    return path
