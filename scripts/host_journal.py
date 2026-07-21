"""Schema-2 journal authority checks and atomic upgrade locking."""

from __future__ import annotations

import os
import pathlib
import re
from collections.abc import Callable
from typing import Any

import host_adapters
import host_state


class JournalError(RuntimeError):
    """Raised before an untrusted journal or concurrent operation can mutate a host."""


ACTIVE_STATUSES = {"in-progress", "recovering", "rollback-incomplete"}
RECOVERABLE_STATUSES = {*ACTIVE_STATUSES, "verified"}
ALL_STATUSES = {*RECOVERABLE_STATUSES, "recovered", "rolled-back"}
FORWARD_ACTIONS = {
    "remove-plugin": True,
    "remove-marketplace": False,
    "add-marketplace": False,
    "install-plugin": True,
}
RECOVERY_ACTIONS = {
    "remove-target-plugin": True,
    "remove-target-marketplace": False,
    "restore-marketplace": False,
    "restore-plugin": True,
}


def lock_path(state_dir: pathlib.Path) -> pathlib.Path:
    resolved = state_dir.expanduser().resolve()
    return resolved.parent / f".{resolved.name}.upgrade.lock"


class UpgradeLock:
    def __init__(self, state_dir: pathlib.Path) -> None:
        self.path = lock_path(state_dir)
        self.fd: int | None = None

    def __enter__(self) -> UpgradeLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, str(os.getpid()).encode("ascii"))
        except FileExistsError as exc:
            raise JournalError(f"upgrade lock is already active: {self.path}") from exc
        return self

    def __exit__(self, *_: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def assert_no_active(state_dir: pathlib.Path) -> None:
    if not state_dir.is_dir():
        return
    for path in sorted(state_dir.glob("*.json")):
        try:
            import json

            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("status") in ACTIVE_STATUSES:
            raise JournalError(f"active transaction journal requires recovery: {path}")


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise JournalError(f"invalid schema-2 transaction journal: {detail}")


def _selector(value: Any) -> bool:
    return isinstance(value, str) and value in {
        f"{package}@divan" for package in host_state.PACKAGES
    }


def _versions(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == set(host_state.PACKAGES) and all(
        isinstance(item, str) and item for item in value.values()
    )


def _evidence(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    strings = ("source", "ref", "root", "commit", "catalog_digest")
    return bool(
        all(isinstance(value.get(key), str) and value[key] for key in strings)
        and re.fullmatch(r"[0-9a-f]{40}", value["commit"])
        and re.fullmatch(r"[0-9a-f]{64}", value["catalog_digest"])
    )


def _pending(value: Any, phase: str, actions: dict[str, bool], hosts: set[str]) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or value.get("phase") != phase:
        return False
    action, host = value.get("action"), value.get("host")
    if action not in actions or host not in hosts:
        return False
    expected = {"phase", "action", "host", "id"} if actions[action] else {
        "phase",
        "action",
        "host",
    }
    return set(value) == expected and (not actions[action] or _selector(value.get("id")))


def _plugin_fingerprint(value: Any, hosts: set[str]) -> bool:
    expected = {
        "host",
        "id",
        "version",
        "marketplace_root",
        "install_path",
        "native_provenance",
    }
    return bool(
        isinstance(value, dict)
        and set(value) == expected
        and value.get("host") in hosts
        and _selector(value.get("id"))
        and isinstance(value.get("version"), str)
        and value.get("version")
        and all(isinstance(value.get(key), str) for key in ("marketplace_root", "install_path"))
        and value.get("native_provenance") is True
    )


def _marketplace_fingerprint(value: Any, hosts: set[str]) -> bool:
    expected = {"host", "source", "ref", "root", "commit", "catalog_digest"}
    return bool(
        isinstance(value, dict)
        and set(value) == expected
        and value.get("host") in hosts
        and _evidence(value)
    )


def _before_rows(
    value: Any, hosts: set[str], target: dict[str, Any], normalize: Callable[[str], str]
) -> bool:
    if not isinstance(value, dict) or set(value) != hosts:
        return False
    expected_selectors = {f"{package}@divan" for package in host_state.PACKAGES}
    for host, row in value.items():
        if not _evidence(row) or not _versions(row.get("contract")):
            return False
        if not isinstance(row.get("plugins"), dict) or set(row["plugins"]) != expected_selectors:
            return False
        if not isinstance(row.get("marketplace"), dict):
            return False
        if normalize(row["source"]) != normalize(target["source"]):
            return False
        if not _snapshot_rows(host, row, normalize):
            return False
    return True


def _snapshot_rows(host: str, snapshot: dict[str, Any], normalize: Callable[[str], str]) -> bool:
    marketplace = snapshot["marketplace"]
    root = host_adapters.marketplace_root(host, marketplace)
    source = host_adapters.marketplace_source(marketplace)
    ref = host_adapters.marketplace_ref(marketplace)
    if root is None or pathlib.Path(root).resolve() != pathlib.Path(snapshot["root"]):
        return False
    if source is not None and normalize(source) != normalize(snapshot["source"]):
        return False
    if ref is not None and ref != snapshot["ref"]:
        return False
    for selector, row in snapshot["plugins"].items():
        if not isinstance(row, dict):
            return False
        try:
            fingerprint = host_state.plugin_fingerprint(
                host, selector, row, pathlib.Path(snapshot["root"])
            )
        except host_state.StateError:
            return False
        package = selector.removesuffix("@divan")
        if fingerprint["version"] != snapshot["contract"][package]:
            return False
    return True


def _created(
    value: Any, hosts: set[str], target: dict[str, Any], normalize: Callable[[str], str]
) -> bool:
    if not isinstance(value, dict) or set(value) != {"marketplaces", "plugins"}:
        return False
    markets, plugins = value["marketplaces"], value["plugins"]
    if not isinstance(markets, list) or not isinstance(plugins, list):
        return False
    if not all(_marketplace_fingerprint(row, hosts) for row in markets):
        return False
    if not all(_plugin_fingerprint(row, hosts) for row in plugins):
        return False
    market_hosts = [row["host"] for row in markets]
    plugin_keys = [(row["host"], row["id"]) for row in plugins]
    if len(market_hosts) != len(set(market_hosts)) or len(plugin_keys) != len(set(plugin_keys)):
        return False
    by_host = {row["host"]: row for row in markets}
    for row in markets:
        if not _created_marketplace_matches(row, target, normalize):
            return False
    return all(_created_plugin_matches(row, by_host, target) for row in plugins)


def _created_marketplace_matches(
    row: dict[str, Any], target: dict[str, Any], normalize: Callable[[str], str]
) -> bool:
    return bool(
        normalize(row["source"]) == normalize(target["source"])
        and all(row[key] == target[key] for key in ("ref", "commit", "catalog_digest"))
    )


def _created_plugin_matches(
    row: dict[str, Any], markets: dict[str, dict[str, Any]], target: dict[str, Any]
) -> bool:
    marketplace = markets.get(row["host"])
    package = row["id"].removesuffix("@divan")
    if marketplace is None or row["marketplace_root"] != marketplace["root"]:
        return False
    expected_path = pathlib.Path(marketplace["root"]) / "plugins" / package
    return bool(
        pathlib.Path(row["install_path"]).resolve() == expected_path.resolve()
        and row["version"] == target["versions"][package]
    )


def _removed(value: Any, hosts: set[str]) -> bool:
    if not isinstance(value, list):
        return False
    for row in value:
        if not isinstance(row, dict) or row.get("host") not in hosts:
            return False
        expected = {"kind", "host", "id"} if row.get("kind") == "plugin" else {
            "kind",
            "host",
        }
        if set(row) != expected or row.get("kind") not in {"plugin", "marketplace"}:
            return False
        if row["kind"] == "plugin" and not _selector(row.get("id")):
            return False
    keys = [(row["kind"], row["host"], row.get("id")) for row in value]
    return len(keys) == len(set(keys))


def validate_schema2(
    path: pathlib.Path, record: dict[str, Any], normalize: Callable[[str], str]
) -> None:
    resolved = path.expanduser().resolve()
    _require(record.get("operation") == "upgrade", "operation")
    _require(record.get("status") in ALL_STATUSES, "status")
    _require(
        isinstance(record.get("transaction_path"), str)
        and pathlib.Path(record["transaction_path"]).expanduser().resolve() == resolved,
        "transaction path",
    )
    host_list = record.get("hosts")
    if not isinstance(host_list, list):
        raise JournalError("invalid schema-2 transaction journal: hosts")
    _require(
        bool(host_list)
        and len(host_list) == len(set(host_list))
        and set(host_list) <= host_state.HOSTS,
        "hosts",
    )
    hosts = set(host_list)
    target = record.get("target")
    if not isinstance(target, dict):
        raise JournalError("invalid schema-2 transaction journal: target evidence")
    _require(_evidence(target) and _versions(target.get("versions")), "target evidence")
    _require(_before_rows(record.get("before_rows"), hosts, target, normalize), "before rows")
    _require(
        _created(record.get("created"), hosts, target, normalize), "created ownership"
    )
    _require(_removed(record.get("removed"), hosts), "removed rows")
    _require(_pending(record.get("pending"), "forward", FORWARD_ACTIONS, hosts), "pending")
    _require(
        _pending(record.get("recovery_pending"), "recovery", RECOVERY_ACTIONS, hosts),
        "recovery pending",
    )
    _require(
        isinstance(record.get("rollback_errors"), list)
        and all(isinstance(item, str) for item in record["rollback_errors"]),
        "rollback errors",
    )
    verified = record.get("verified")
    _require(
        isinstance(verified, dict)
        and set(verified) <= hosts
        and all(isinstance(row, dict) for row in verified.values()),
        "verified hosts",
    )
