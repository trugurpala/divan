"""Coordinate schema-1 install and schema-2 upgrade recovery."""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import Any

import host_install_journal
import host_transactions

LegacyRecovery = Callable[[pathlib.Path, dict[str, Any]], None]


def recover(
    path: pathlib.Path,
    record: dict[str, Any],
    install_io: host_install_journal.InstallIO,
    upgrade_io: host_transactions.RecoveryIO,
    recover_legacy: LegacyRecovery,
    confirmation: str | None = None,
) -> dict[str, Any]:
    """Recover one already-loaded transaction under the caller's host lock."""
    if record["schema"] == 1:
        host_install_journal.validate(record, path)
        recover_legacy(path, record)
        return host_install_journal.recover_native(
            path,
            record,
            install_io,
            confirmation,
        )
    if confirmation is not None:
        raise host_transactions.TransactionError(
            "--confirm-pending-marketplace applies only to schema-1 install recovery"
        )
    return host_transactions.recover_upgrade(path, record, upgrade_io)
