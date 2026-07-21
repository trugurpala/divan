"""Provenance proof and forward orchestration for Divan host upgrades."""

from __future__ import annotations

import json
import pathlib
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import host_adapters
import host_transactions


@dataclass(frozen=True)
class UpgradeIO:
    marketplace_rows: Callable[[str], dict[str, dict[str, Any]]]
    plugin_rows: Callable[[str], dict[str, dict[str, Any]]]
    run: Callable[[list[str]], str]
    verify_host: Callable[[str, Any, dict[str, dict[str, Any]]], dict[str, Any]]
    rollback: Callable[[pathlib.Path], dict[str, Any]]
    normalize_source: Callable[[str], str]


def _catalog_versions(root: pathlib.Path, packages: tuple[str, ...]) -> dict[str, str]:
    path = root / ".agents" / "plugins" / "marketplace.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise host_transactions.TransactionError(
            f"cannot prove marketplace version contract: {path}"
        ) from exc
    versions: dict[str, str] = {}
    for row in value.get("plugins", []):
        if not isinstance(row, dict):
            continue
        name, version = row.get("name"), row.get("version")
        if isinstance(name, str) and isinstance(version, str):
            versions[name] = version
    if set(versions) != set(packages):
        raise host_transactions.TransactionError(
            "marketplace version contract does not define the expected packages"
        )
    return versions


def marketplace_identity(
    host: str, row: dict[str, Any], run: Callable[[list[str]], str]
) -> tuple[str, str]:
    root = host_adapters.marketplace_root(host, row)
    if root is None:
        raise host_transactions.TransactionError(
            f"{host}: divan marketplace root is missing"
        )
    source = run(["git", "-C", root, "remote", "get-url", "origin"]).strip()
    reported_ref = host_adapters.marketplace_ref(row)
    command = ["git", "-C", root, "rev-parse", "HEAD"]
    if not isinstance(reported_ref, str) or not re.fullmatch(r"[0-9a-f]{40}", reported_ref):
        command = ["git", "-C", root, "describe", "--tags", "--exact-match"]
    actual_ref = run(command).strip()
    if reported_ref is not None and reported_ref != actual_ref:
        raise host_transactions.TransactionError(
            f"{host}: marketplace ref cannot be proven"
        )
    return source, actual_ref


def _path_is_owned(root: pathlib.Path, value: str | None) -> bool:
    if value is None:
        return False
    try:
        pathlib.Path(value).resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _capture_owned_host(
    host: str, options: Any, packages: tuple[str, ...], io: UpgradeIO
) -> dict[str, Any]:
    marketplace = io.marketplace_rows(host).get("divan")
    if marketplace is None:
        raise host_transactions.TransactionError(f"{host}: divan marketplace is missing")
    source, ref = marketplace_identity(host, marketplace, io.run)
    if io.normalize_source(source) != io.normalize_source(options.source):
        raise host_transactions.TransactionError(
            f"{host}: marketplace source does not match requested repository"
        )
    root_value = host_adapters.marketplace_root(host, marketplace)
    assert root_value is not None
    contract = _catalog_versions(pathlib.Path(root_value), packages)
    rows = io.plugin_rows(host)
    owned = {key: row for key, row in rows.items() if key.endswith("@divan")}
    if set(owned) != {f"{package}@divan" for package in contract}:
        raise host_transactions.TransactionError(
            f"{host}: installed Divan package set does not match marketplace contract"
        )
    _prove_plugins(host, pathlib.Path(root_value), contract, owned)
    return {
        "source": source,
        "ref": ref,
        "root": root_value,
        "marketplace": marketplace,
        "plugins": owned,
        "contract": contract,
    }


def _prove_plugins(
    host: str,
    root: pathlib.Path,
    contract: dict[str, str],
    owned: dict[str, dict[str, Any]],
) -> None:
    for selector, row in owned.items():
        package = selector.removesuffix("@divan")
        valid = (
            row.get("version") == contract[package]
            and row.get("enabled") is True
            and host_adapters.plugin_provenance_valid(host, row)
            and _path_is_owned(root, host_adapters.plugin_install_path(host, row))
        )
        if not valid:
            raise host_transactions.TransactionError(
                f"{host}: {selector} does not match marketplace version contract"
            )


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
    path: pathlib.Path, record: dict[str, Any], host: str, io: UpgradeIO
) -> None:
    for selector in record["before_rows"][host]["plugins"]:
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
    _mutation(
        path,
        record,
        {"phase": "forward", "action": "add-marketplace", "host": host},
        host_adapters.add_marketplace_command(host, options.source, options.ref),
        record["created"]["marketplaces"],
        host,
        io,
    )
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
    _mutation(
        path,
        record,
        {"phase": "forward", "action": "install-plugin", "host": host, "id": selector},
        host_adapters.install_command(host, package),
        record["created"]["plugins"],
        {"host": host, "id": selector},
        io,
    )


def _matches_target(before: dict[str, Any], target: dict[str, Any], io: UpgradeIO) -> bool:
    return bool(
        io.normalize_source(before["source"]) == io.normalize_source(target["source"])
        and before["ref"] == target["ref"]
        and before["contract"] == target["versions"]
    )


def _apply_host(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    options: Any,
    packages: tuple[str, ...],
    expected: dict[str, dict[str, Any]],
    io: UpgradeIO,
) -> None:
    if not _matches_target(record["before_rows"][host], record["target"], io):
        _remove_previous(path, record, host, io)
        _install_target(path, record, host, options, packages, io)
    record["verified"][host] = io.verify_host(host, options, expected)
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
) -> dict[str, Any]:
    versions = {package: row["version"] for package, row in expected.items()}
    record = _record(options, packages, versions)
    if not options.execute:
        return record
    record["before_rows"] = {
        host: _capture_owned_host(host, options, packages, io) for host in options.hosts
    }
    if all(_matches_target(before, record["target"], io) for before in record["before_rows"].values()):
        record["status"] = "no-op"
        return record
    options.state_dir.mkdir(parents=True, exist_ok=True)
    path = _start_transaction(options, record)
    try:
        for host in options.hosts:
            _apply_host(path, record, host, options, packages, expected, io)
    except BaseException as exc:
        _fail(path, exc, io)
    record["status"] = "verified"
    record["finished_at"] = datetime.now(UTC).isoformat()
    host_transactions.persist_record(path, record)
    return record


def _start_transaction(options: Any, record: dict[str, Any]) -> pathlib.Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = options.state_dir / f"upgrade-{stamp}-{uuid.uuid4().hex[:8]}.json"
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
