"""Complete fail-closed authority for schema-1 install journals."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import host_adapters
import host_state


class AuthorityError(RuntimeError):
    """Raised when a schema-1 journal cannot prove mutation authority."""


def validate(record: dict[str, Any], expected_path: pathlib.Path | None = None) -> None:
    _header(record)
    hosts = record["hosts"]
    assert isinstance(hosts, list)
    transaction = _transaction_path(record.get("transaction_path"), expected_path)
    target, created, before = record.get("target"), record.get("created"), record.get("before")
    _require(isinstance(target, dict) and _target(target), "fingerprint authority")
    _require(isinstance(created, dict) and isinstance(before, dict), "ownership authority")
    assert isinstance(target, dict) and isinstance(created, dict) and isinstance(before, dict)
    _require(_before(before, hosts, record["status"] == "verified"), "before snapshot")
    markets, plugins = created.get("marketplaces"), created.get("plugins")
    _require(isinstance(markets, list) and isinstance(plugins, list), "created fingerprints")
    assert isinstance(markets, list) and isinstance(plugins, list)
    _require(_created_marketplaces(markets, target, before), "marketplace fingerprints")
    _require(_created_plugins(plugins, markets, target, before), "plugin fingerprints")
    _require(_pending(record.get("pending"), set(before), record["status"]), "pending mutation")
    _validate_legacy(record, transaction, set(hosts))


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise AuthorityError(f"install journal {detail} is invalid")


def _header(record: dict[str, Any]) -> None:
    _require(record.get("schema") == 1, "schema")
    if record.get("fingerprint_schema") != 1:
        raise AuthorityError("legacy install journal lacks exact fingerprints")
    _require(record.get("operation") == "install", "operation")
    _require(
        record.get("status") in {
            "in-progress", "recovering", "rollback-incomplete", "verified",
            "recovered", "rolled-back",
        },
        "status",
    )
    _require(
        record.get("hosts") in (["claude"], ["codex"], ["claude", "codex"]),
        "hosts",
    )


def _transaction_path(value: Any, expected: pathlib.Path | None) -> pathlib.Path:
    _require(isinstance(value, str) and bool(value), "transaction path")
    assert isinstance(value, str)
    raw = pathlib.Path(value).expanduser()
    resolved = raw.resolve()
    _require(
        raw.is_absolute() and raw == resolved
        and (expected is None or resolved == expected.resolve()),
        "transaction path",
    )
    return resolved


def _before(value: Any, hosts: list[str], require_full: bool) -> bool:
    if not isinstance(value, dict) or not set(value) <= set(hosts):
        return False
    if require_full and set(value) != set(hosts):
        return False
    for row in value.values():
        if not isinstance(row, dict) or set(row) != {"marketplaces", "plugins"}:
            return False
        for key in ("marketplaces", "plugins"):
            items = row[key]
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                return False
            if len(items) != len(set(items)):
                return False
    return True


def _pending(value: Any, captured: set[str], status: str) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or status in {"recovered", "rolled-back"}:
        return False
    phase, action, host = value.get("phase"), value.get("action"), value.get("host")
    if phase not in {"forward", "recovery"} or host not in captured:
        return False
    if action in {"install-plugin", "remove-plugin"}:
        return set(value) == {"phase", "action", "host", "id"} and _selector(value.get("id"))
    if action in {"legacy-migration", "recover-legacy"}:
        return set(value) == {"phase", "action", "host", "journal"} and host == "codex"
    return action in {"add-marketplace", "remove-marketplace"} and set(value) == {
        "phase", "action", "host",
    }


def _selector(value: Any) -> bool:
    return isinstance(value, str) and value in {
        f"{package}@divan" for package in host_state.PACKAGES
    }


def _legacy_path(record: dict[str, Any]) -> str | None:
    pending = record.get("pending")
    if isinstance(pending, dict) and pending.get("action") in {
        "legacy-migration", "recover-legacy",
    }:
        value = pending.get("journal")
        return value if isinstance(value, str) else None
    completed = record.get("legacy_migration")
    result = completed.get("result") if isinstance(completed, dict) else None
    value = result.get("journal") if isinstance(result, dict) else None
    return value if isinstance(value, str) else None


def _validate_legacy(
    record: dict[str, Any], transaction: pathlib.Path, hosts: set[str]
) -> None:
    journal_text = _legacy_path(record)
    if journal_text is None:
        _require("legacy_migration" not in record, "linked legacy journal identity")
        return
    journal = pathlib.Path(journal_text).expanduser()
    resolved = journal.resolve()
    _require("codex" in hosts and journal.is_absolute() and journal == resolved, "legacy path")
    _require(
        resolved.parent == transaction.parent and resolved.name.startswith("legacy-"),
        "linked legacy journal containment",
    )
    if not resolved.is_file():
        raise AuthorityError("linked legacy journal is missing")
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityError("linked legacy journal is unreadable") from exc
    _require(
        isinstance(value, dict)
        and value.get("schema") == 1
        and value.get("kind") == "migration"
        and value.get("journal") == str(resolved),
        "linked legacy journal identity",
    )


def _target(value: Any) -> bool:
    expected = {"source", "ref", "root", "commit", "catalog_digest", "versions"}
    return bool(
        isinstance(value, dict) and set(value) == expected
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
        if "divan" in before[row["host"]]["marketplaces"]:
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
        if not _selector(selector):
            return False
        package = selector.removesuffix("@divan")
        if row["version"] != target["versions"][package]:
            return False
        if selector in before[row["host"]]["plugins"]:
            return False
        if row["native_provenance"] is not True or row["marketplace_root"] != roots[row["host"]]:
            return False
        if host_adapters.native_install_path(
            row["host"], row["install_path"], pathlib.Path(roots[row["host"]]),
            package, row["version"], target["source"],
        ) is None:
            return False
        keys.append((row["host"], selector))
    return len(keys) == len(set(keys))
