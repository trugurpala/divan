"""Marketplace ownership and pending-add recovery for schema-1 installs."""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections.abc import Callable
from dataclasses import dataclass
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


def capture_marketplace(
    record: dict[str, Any],
    host: str,
    io: InstallIO,
    row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = marketplace_evidence(record, host, io, row)
    target = record["target"]
    if evidence["contract"] != target["versions"] or any(
        evidence[key] != target[key] for key in ("commit", "catalog_digest")
    ):
        raise InstallJournalError(f"{host}: created marketplace fingerprint is not target")
    return host_state.marketplace_fingerprint(host, evidence)


def marketplace_evidence(
    record: dict[str, Any],
    host: str,
    io: InstallIO,
    row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if row is None:
        row = io.marketplace_rows(host).get("divan")
    if row is None:
        raise InstallJournalError(f"{host}: created marketplace is missing")
    target = record["target"]
    try:
        return host_state.marketplace_evidence(
            host,
            row,
            target["source"],
            target["ref"],
            io.run,
            io.normalize_source,
        )
    except host_state.StateError as exc:
        raise InstallJournalError(str(exc)) from exc


def resume_pending_removal(
    path: pathlib.Path,
    record: dict[str, Any],
    pending: dict[str, Any],
    io: InstallIO,
) -> None:
    host = pending["host"]
    if any(entry["host"] == host for entry in record["created"]["marketplaces"]):
        return
    receipt = pending.get("marketplace")
    recovered = _recover_pending_codex_marketplace(
        path,
        record,
        host,
        io,
        io.marketplace_rows(host).get("divan"),
        receipt if isinstance(receipt, dict) else None,
    )
    if not recovered:
        raise InstallJournalError(
            f"{host}: pending marketplace recovery receipt cannot be proven"
        )


def promote_pending(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: InstallIO,
    confirmation: str | None,
) -> bool:
    _require_absent_before(record, host)
    row = io.marketplace_rows(host).get("divan")
    if row is None:
        return True
    try:
        marketplace = capture_marketplace(record, host, io, row)
    except InstallJournalError as exc:
        recovered = _recover_pending_codex_marketplace(
            path,
            record,
            host,
            io,
            row,
            confirmation=confirmation,
        )
        if not recovered:
            raise exc
        return False
    if marketplace not in record["created"]["marketplaces"]:
        record["created"]["marketplaces"].append(marketplace)
    return True


def _require_absent_before(record: dict[str, Any], host: str) -> None:
    before = record["before"][host]
    has_divan = "divan" in before["marketplaces"] or any(
        selector.endswith("@divan") for selector in before["plugins"]
    )
    if has_divan:
        raise InstallJournalError(
            f"{host}: pending Divan state existed before the transaction"
        )


def _recover_pending_codex_marketplace(
    path: pathlib.Path,
    record: dict[str, Any],
    host: str,
    io: InstallIO,
    row: dict[str, Any] | None,
    receipt: dict[str, Any] | None = None,
    confirmation: str | None = None,
) -> bool:
    if host != "codex":
        return False
    _require_absent_before(record, host)
    if row is None:
        record["pending"] = None
        host_transactions.persist_record(path, record)
        return True
    if not _has_native_receipt(host, row):
        return False
    evidence = marketplace_evidence(record, host, io, row)
    marketplace = host_state.marketplace_fingerprint(host, evidence)
    _require_expected_receipt(record, marketplace, receipt)
    _require_target_contract(record, evidence)
    _require_no_divan_plugins(io, host)
    if receipt is None:
        _require_confirmation(path, marketplace, confirmation)
    if not _require_unchanged_live_marketplace(record, host, io, marketplace):
        record["pending"] = None
        host_transactions.persist_record(path, record)
        return True
    if receipt is None:
        record["pending"] = {
            "phase": "recovery",
            "action": "remove-marketplace",
            "host": host,
            "marketplace": marketplace,
        }
        host_transactions.persist_record(path, record)
    command = " ".join(host_adapters.remove_marketplace_command(host))
    raise InstallJournalError(
        "codex: pending marketplace fingerprint is recorded, but the host CLI "
        "can remove only by name; to avoid deleting a concurrent replacement, "
        f"inspect the reported checkout, run `{command}` manually, then rerun "
        "the recovery command"
    )


def _has_native_receipt(host: str, row: dict[str, Any]) -> bool:
    root = host_adapters.marketplace_root(host, row)
    metadata = (
        pathlib.Path(root) / ".codex-marketplace-install.json"
        if root is not None
        else None
    )
    return metadata is not None and metadata.is_file()


def _require_expected_receipt(
    record: dict[str, Any],
    marketplace: dict[str, Any],
    receipt: dict[str, Any] | None,
) -> None:
    if receipt is not None and marketplace != receipt:
        raise InstallJournalError(
            "codex: pending marketplace recovery refuses replaced marketplace"
        )
    pending = record.get("pending")
    if (
        receipt is None
        and isinstance(pending, dict)
        and pending.get("phase") == "recovery"
    ):
        raise InstallJournalError(
            "codex: pending marketplace recovery receipt cannot be proven"
        )


def _require_target_contract(
    record: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    if evidence["contract"] != record["target"]["versions"]:
        raise InstallJournalError(
            "codex: pending marketplace contract is not the install target"
        )


def _require_no_divan_plugins(io: InstallIO, host: str) -> None:
    if any(selector.endswith("@divan") for selector in io.plugin_rows(host)):
        raise InstallJournalError(
            "codex: pending marketplace recovery refuses installed Divan plugins"
        )


def _require_confirmation(
    path: pathlib.Path,
    marketplace: dict[str, Any],
    confirmation: str | None,
) -> None:
    expected = marketplace_confirmation(path, marketplace)
    if confirmation != expected:
        raise InstallJournalError(
            "codex: pending marketplace ownership is ambiguous; "
            f"root={marketplace['root']}, commit={marketplace['commit']}, "
            f"catalog={marketplace['catalog_digest']}; rerun recovery with "
            f"--confirm-pending-marketplace {expected}"
        )


def _require_unchanged_live_marketplace(
    record: dict[str, Any],
    host: str,
    io: InstallIO,
    expected: dict[str, Any],
) -> bool:
    current = io.marketplace_rows(host).get("divan")
    if current is None:
        return False
    evidence = marketplace_evidence(record, host, io, current)
    if host_state.marketplace_fingerprint(host, evidence) != expected:
        raise InstallJournalError(
            "codex: pending marketplace recovery refuses replaced marketplace"
        )
    _require_no_divan_plugins(io, host)
    return True


def marketplace_confirmation(path: pathlib.Path, marketplace: dict[str, Any]) -> str:
    """Bind explicit recovery approval to one transaction and checkout fingerprint."""
    evidence = {
        "transaction": str(path.expanduser().resolve()),
        "marketplace": marketplace,
    }
    encoded = json.dumps(
        evidence,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
