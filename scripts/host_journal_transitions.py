"""Cross-field state-machine invariants for schema-2 host journals."""

from __future__ import annotations

from typing import Any

import host_state

SELECTORS = [f"{package}@divan" for package in host_state.PACKAGES]
RECOVERY_STATUSES = {"recovering", "rollback-incomplete"}
TERMINAL_STATUSES = {"verified", "recovered", "rolled-back"}


def valid(record: dict[str, Any]) -> bool:
    if not _ledger_transitions(record):
        return False
    pending, recovery = record.get("pending"), record.get("recovery_pending")
    status = record.get("status")
    if pending is not None and recovery is not None:
        return False
    if pending is not None and (status != "in-progress" or not _forward(record, pending)):
        return False
    if recovery is not None and (
        status not in RECOVERY_STATUSES or not _recovery(record, recovery)
    ):
        return False
    if status in TERMINAL_STATUSES and (pending is not None or recovery is not None):
        return False
    if status == "in-progress" and recovery is not None:
        return False
    if status in RECOVERY_STATUSES and pending is not None:
        return False
    return True


def _ledger_transitions(record: dict[str, Any]) -> bool:
    for host in record["hosts"]:
        removed_plugins = _removed_plugins(record, host)
        created_plugins = _created_plugins(record, host)
        removed_market = _has_removed_marketplace(record, host)
        created_market = _has_created_marketplace(record, host)
        if removed_plugins != SELECTORS[: len(removed_plugins)]:
            return False
        if created_plugins != SELECTORS[: len(created_plugins)]:
            return False
        if removed_market and removed_plugins != SELECTORS:
            return False
        if created_market and (not removed_market or removed_plugins != SELECTORS):
            return False
        if created_plugins and not created_market:
            return False
    return True


def _forward(record: dict[str, Any], pending: dict[str, Any]) -> bool:
    host, action = pending["host"], pending["action"]
    removed = _removed_plugins(record, host)
    created = _created_plugins(record, host)
    removed_market = _has_removed_marketplace(record, host)
    created_market = _has_created_marketplace(record, host)
    if action == "remove-plugin":
        return not removed_market and not created_market and pending["id"] == _next(removed)
    if action == "remove-marketplace":
        return removed == SELECTORS and not removed_market and not created_market
    if action == "add-marketplace":
        return removed == SELECTORS and removed_market and not created_market and not created
    if action == "install-plugin":
        return (
            removed == SELECTORS
            and removed_market
            and created_market
            and pending["id"] == _next(created)
        )
    return False


def _recovery(record: dict[str, Any], pending: dict[str, Any]) -> bool:
    host, action = pending["host"], pending["action"]
    if action == "remove-target-plugin":
        return any(
            row["host"] == host and row["id"] == pending["id"]
            for row in record["created"]["plugins"]
        )
    if action == "remove-target-marketplace":
        return _has_created_marketplace(record, host)
    if action in {"restore-marketplace", "restore-plugin"}:
        return host in _affected_hosts(record)
    return False


def _next(prefix: list[str]) -> str | None:
    return SELECTORS[len(prefix)] if len(prefix) < len(SELECTORS) else None


def _removed_plugins(record: dict[str, Any], host: str) -> list[str]:
    return [
        row["id"]
        for row in record["removed"]
        if row["host"] == host and row["kind"] == "plugin"
    ]


def _created_plugins(record: dict[str, Any], host: str) -> list[str]:
    return [row["id"] for row in record["created"]["plugins"] if row["host"] == host]


def _has_removed_marketplace(record: dict[str, Any], host: str) -> bool:
    return any(
        row["host"] == host and row["kind"] == "marketplace" for row in record["removed"]
    )


def _has_created_marketplace(record: dict[str, Any], host: str) -> bool:
    return any(row["host"] == host for row in record["created"]["marketplaces"])


def _affected_hosts(record: dict[str, Any]) -> set[str]:
    hosts = {row["host"] for row in record["removed"]}
    hosts.update(row["host"] for row in record["created"]["marketplaces"])
    hosts.update(row["host"] for row in record["created"]["plugins"])
    return hosts
