"""Fail-closed discovery of active and terminal host transaction journals."""

from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from typing import Any

import host_state


class ScanError(RuntimeError):
    """Raised when a transaction file cannot be classified safely."""


UpgradeValidator = Callable[[pathlib.Path, dict[str, Any], Callable[[str], str]], None]


def assert_no_active(
    state_dir: pathlib.Path,
    normalize: Callable[[str], str],
    validate_upgrade: UpgradeValidator,
    active_statuses: set[str],
) -> None:
    if not state_dir.is_dir():
        return
    paths = [*state_dir.glob("install-*.json"), *state_dir.glob("upgrade-*.json")]
    for path in sorted(paths):
        record = _read(path)
        if record.get("status") in active_statuses:
            raise ScanError(f"active transaction journal requires recovery: {path}")
        if path.name.startswith("upgrade-"):
            validate_upgrade(path, record, normalize)
        else:
            _validate_terminal_schema1(path, record)


def _read(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScanError(f"transaction journal is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise ScanError(f"transaction journal is malformed: {path}")
    return value


def _validate_terminal_schema1(path: pathlib.Path, record: dict[str, Any]) -> None:
    _require(record.get("schema") == 1, "install schema")
    status = record.get("status")
    _require(status in {"verified", "recovered", "rolled-back"}, "install status")
    _require(
        isinstance(record.get("transaction_path"), str)
        and pathlib.Path(record["transaction_path"]).expanduser().resolve() == path.resolve(),
        "install transaction path",
    )
    hosts = record.get("hosts")
    _require(_valid_hosts(hosts), "install hosts")
    assert isinstance(hosts, list)
    _require(record.get("pending") is None, "install pending")
    before = record.get("before")
    _require(
        _schema1_before(before, set(hosts), require_full=status == "verified"),
        "install before",
    )
    assert isinstance(before, dict)
    if record.get("fingerprint_schema") == 1:
        try:
            __import__("host_install_journal").validate(record, path)
        except RuntimeError as exc:
            raise ScanError(f"invalid terminal transaction journal: {exc}") from exc
    else:
        _require(_schema1_created(record.get("created"), set(before)), "install created")


def _valid_hosts(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and all(isinstance(host, str) for host in value)
        and len(value) == len(set(value))
        and set(value) <= host_state.HOSTS
    )


def _schema1_before(value: Any, hosts: set[str], *, require_full: bool) -> bool:
    if not isinstance(value, dict):
        return False
    captured = set(value)
    if require_full and captured != hosts:
        return False
    if not require_full and not captured <= hosts:
        return False
    return all(
        isinstance(row, dict)
        and set(row) == {"marketplaces", "plugins"}
        and _string_rows(row["marketplaces"])
        and _string_rows(row["plugins"])
        for row in value.values()
    )


def _string_rows(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and all(isinstance(item, str) and item for item in value)
        and len(value) == len(set(value))
    )


def _schema1_created(value: Any, hosts: set[str]) -> bool:
    if not isinstance(value, dict) or set(value) != {"marketplaces", "plugins"}:
        return False
    markets, plugins = value["marketplaces"], value["plugins"]
    if not isinstance(markets, list) or not isinstance(plugins, list):
        return False
    if not all(host in hosts for host in markets) or len(markets) != len(set(markets)):
        return False
    valid = all(
        isinstance(row, dict)
        and set(row) == {"host", "id"}
        and row["host"] in hosts
        and row["host"] in markets
        and _selector(row["id"])
        for row in plugins
    )
    keys = [(row["host"], row["id"]) for row in plugins if isinstance(row, dict)]
    return valid and len(keys) == len(set(keys))


def _selector(value: Any) -> bool:
    return isinstance(value, str) and value in {
        f"{package}@divan" for package in host_state.PACKAGES
    }


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ScanError(f"invalid terminal transaction journal: {detail}")
