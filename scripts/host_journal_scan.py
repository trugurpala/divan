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
    _require(record.get("status") in {"verified", "recovered", "rolled-back"}, "install status")
    _require(
        isinstance(record.get("transaction_path"), str)
        and pathlib.Path(record["transaction_path"]).expanduser().resolve() == path.resolve(),
        "install transaction path",
    )
    hosts = record.get("hosts")
    _require(_valid_hosts(hosts), "install hosts")
    assert isinstance(hosts, list)
    _require(record.get("pending") is None, "install pending")
    _require(_schema1_before(record.get("before"), set(hosts)), "install before")
    _require(_schema1_created(record.get("created"), set(hosts)), "install created")


def _valid_hosts(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and all(isinstance(host, str) for host in value)
        and len(value) == len(set(value))
        and set(value) <= host_state.HOSTS
    )


def _schema1_before(value: Any, hosts: set[str]) -> bool:
    if not isinstance(value, dict) or set(value) != hosts:
        return False
    return all(
        isinstance(row, dict)
        and isinstance(row.get("marketplaces"), list)
        and isinstance(row.get("plugins"), list)
        and all(isinstance(item, str) for item in [*row["marketplaces"], *row["plugins"]])
        for row in value.values()
    )


def _schema1_created(value: Any, hosts: set[str]) -> bool:
    if not isinstance(value, dict) or set(value) != {"marketplaces", "plugins"}:
        return False
    markets, plugins = value["marketplaces"], value["plugins"]
    if not isinstance(markets, list) or not isinstance(plugins, list):
        return False
    if not all(host in hosts for host in markets):
        return False
    return all(
        isinstance(row, dict)
        and set(row) == {"host", "id"}
        and row["host"] in hosts
        and _selector(row["id"])
        for row in plugins
    )


def _selector(value: Any) -> bool:
    return isinstance(value, str) and value in {
        f"{package}@divan" for package in host_state.PACKAGES
    }


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ScanError(f"invalid terminal transaction journal: {detail}")
