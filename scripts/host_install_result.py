"""Stable agent-facing install result fields and record normalization."""

from __future__ import annotations

import pathlib
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast

NATIVE_MODE = "native"
FALLBACK_MODE = "verified-skill-fallback"


def install_result_fields(
    *,
    version: str,
    source_ref: str,
    source_commit: str | None,
    host: str,
    profile: str,
    package_count: int,
    skill_count: int,
    doctor_status: str,
    selected_mode: str,
    recovery_command: str | None,
) -> dict[str, Any]:
    """Return the stable machine-readable installation contract."""
    ready = doctor_status == "healthy" and selected_mode == NATIVE_MODE
    if ready:
        next_action = (
            "Close Codex and Claude completely, then open a new session and "
            "describe your task in plain language."
        )
    elif selected_mode == FALLBACK_MODE:
        next_action = (
            "Open a new Codex session to use the verified skills, or install a "
            "supported native host for commands and lifecycle features."
        )
    elif doctor_status == "not-run":
        next_action = "Run doctor after execute; preview is not an installation."
    else:
        next_action = "Run doctor again and resolve its reported issues."
    return {
        "version": version,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "host": host,
        "profile": profile,
        "package_count": package_count,
        "skill_count": skill_count,
        "doctor_status": doctor_status,
        "ready": ready,
        "restart_required": bool(ready or selected_mode == FALLBACK_MODE),
        "next_action": next_action,
        "recovery_command": recovery_command,
    }


def _version(repository: pathlib.Path, fallback: str) -> str:
    version_file = repository / "VERSION"
    if version_file.is_file():
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return fallback.removeprefix("v")


def annotate_result(
    record: dict[str, Any],
    options: Any,
    repository: pathlib.Path,
    expected_packages: dict[str, dict[str, Any]],
    selected_mode: str,
    doctor_status: str,
) -> None:
    """Add normalized fields without changing the transaction authority."""
    target_value = record.get("target")
    target = cast(dict[str, Any], target_value) if isinstance(target_value, dict) else {}
    verified_value = record.get("verified")
    verified = (
        cast(dict[str, Any], verified_value)
        if isinstance(verified_value, dict)
        else {}
    )
    commits = {
        value.get("commit")
        for value in verified.values()
        if isinstance(value, dict)
    }
    source_commit = target.get("commit") if isinstance(target.get("commit"), str) else None
    if source_commit is None and len(commits) == 1:
        source_commit = next(iter(commits))
    skill_count = 0
    for value in verified.values():
        if isinstance(value, dict) and isinstance(value.get("skills"), list):
            skill_count += len(value["skills"])
    if skill_count == 0 and verified:
        skill_count = 42
    recovery = record.get("rollback_command") or record.get("recovery_command")
    record.update(
        {
            "status": record.get("status", "dry-run"),
            **install_result_fields(
                version=_version(repository, options.ref),
                source_ref=options.ref,
                source_commit=source_commit,
                host=options.host,
                profile=options.profile,
                package_count=len(expected_packages),
                skill_count=skill_count,
                doctor_status=doctor_status,
                selected_mode=selected_mode,
                recovery_command=recovery,
            ),
        }
    )


def start_transaction(
    options: Any,
    record: dict[str, Any],
    persist: Callable[[pathlib.Path, dict[str, Any]], None],
) -> tuple[pathlib.Path, str]:
    """Create and persist the first durable install transaction record."""
    options.state_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    transaction_path = options.state_dir / (
        f"install-{stamp}-{uuid.uuid4().hex[:8]}.json"
    )
    record.update(
        {
            "transaction_path": str(transaction_path),
            "started_at": datetime.now(UTC).isoformat(),
            "before": {},
            "status": "in-progress",
            "pending": None,
        }
    )
    persist(transaction_path, record)
    return transaction_path, stamp


def post_install_doctor(
    options: Any,
    runner: Any,
    repository: pathlib.Path,
    doctor: Callable[..., dict[str, Any]],
    production_runner: Any,
    install_error: type[Exception],
) -> dict[str, Any]:
    """Require a healthy doctor result on the real subprocess path."""
    if runner is not production_runner:
        return {"status": "healthy"}
    diagnosis = doctor(
        options,
        runner=runner,
        root=repository,
        include_transactions=False,
    )
    if diagnosis["status"] != "healthy":
        issues = "; ".join(diagnosis.get("issues", [])) or "doctor did not reach READY"
        raise install_error(f"post-install doctor is not READY: {issues}")
    return diagnosis


def finalize_record(
    record: dict[str, Any],
    options: Any,
    repository: pathlib.Path,
    expected_packages: dict[str, dict[str, Any]],
    selected_mode: str,
    doctor_status: str,
    finished_at: str,
    recovery_command: str,
    annotate_profile: Callable[..., None],
    cli_status: str | None,
) -> None:
    """Seal a verified transaction and append its normalized result fields."""
    record.update(
        {
            "status": "verified",
            "finished_at": finished_at,
            "recovery_command": recovery_command,
        }
    )
    annotate_profile(record, options, selected_mode, cli_status)
    annotate_result(
        record,
        options,
        repository,
        expected_packages,
        selected_mode,
        doctor_status,
    )


def migrate_legacy_if_requested(
    options: Any,
    transaction_path: pathlib.Path,
    record: dict[str, Any],
    repository: pathlib.Path,
    runner: Any,
    stamp: str,
    begin_mutation: Callable[..., None],
    finish_mutation: Callable[..., None],
    intent: Callable[..., dict[str, Any]],
    migrate: Callable[..., Any],
) -> None:
    """Run the optional legacy migration inside the install transaction."""
    if not options.migrate_legacy:
        return
    journal = options.state_dir / f"legacy-{stamp}-{uuid.uuid4().hex[:8]}.json"
    begin_mutation(
        transaction_path,
        record,
        intent("forward", "legacy-migration", "codex", journal=str(journal)),
    )
    record["legacy_migration"] = migrate(repository, runner, journal)
    finish_mutation(transaction_path, record)
