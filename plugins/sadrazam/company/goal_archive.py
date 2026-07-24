"""Transactional archive for completed Divan Project OS goals."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
from datetime import UTC, datetime
from typing import Any

import goals
import project_os
import receipts

ARCHIVABLE_STATES = frozenset({"VERIFIED", "RELEASED", "OBSERVED"})
MAX_FILES = 200
MAX_FILE_BYTES = 1024 * 1024


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _plan_digest(value: dict[str, Any]) -> str:
    material = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{_sha256(material)}"


def _blocked(
    root: pathlib.Path, identifier: str, errors: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation": "goal-archive",
        "status": "BLOCKED",
        "project": root.name,
        "goal_id": identifier,
        "errors": errors,
        "execute_required": True,
    }


def _real_files(root: pathlib.Path) -> tuple[list[pathlib.Path], list[str]]:
    if root.is_symlink() or not root.is_dir():
        return [], [f"{root.name} goal directory is unavailable or unsafe"]
    files: list[pathlib.Path] = []
    errors: list[str] = []
    for candidate in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if candidate.is_symlink():
            errors.append(f"{candidate.name} is a symlink")
        elif candidate.is_file():
            if candidate.stat().st_size > MAX_FILE_BYTES:
                errors.append(f"{candidate.name} exceeds 1 MiB")
            files.append(candidate)
        elif not candidate.is_dir():
            errors.append(f"{candidate.name} has an unsupported file type")
        if len(files) > MAX_FILES:
            errors.append("goal archive exceeds 200 files")
            break
    return files, errors


def _receipt_binding_errors(
    receipt_path: pathlib.Path, spec_root: pathlib.Path
) -> list[str]:
    """Bind mutable receipt identity fields back to the hashed goal spec."""
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        spec = (spec_root / "spec.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [f"goal identity cannot be verified: {error}"]
    intent = receipt.get("intent")
    target = receipt.get("target")
    expected = (
        f"## Intent\n\n{intent}\n\n## Target\n\n{target}\n\n"
        if isinstance(intent, str) and isinstance(target, str)
        else ""
    )
    if not expected or expected not in spec:
        return ["receipt intent or target does not match the hashed goal spec"]
    return []


def build_archive_plan(
    project: pathlib.Path | str, identifier: str
) -> dict[str, Any]:
    """Build a deterministic, read-only archive plan for a completed goal."""
    root = pathlib.Path(project).resolve()
    try:
        spec_root, evidence_root, receipt_path = goals._goal_paths(
            root, identifier
        )
    except ValueError as error:
        return _blocked(root, str(identifier), [str(error)])
    verification = receipts.verify_receipt(receipt_path)
    if not verification["ok"]:
        return _blocked(root, identifier, list(verification["errors"]))
    state = verification.get("state")
    if state not in ARCHIVABLE_STATES:
        return _blocked(
            root, identifier, [f"goal state {state} is not archivable"]
        )
    spec_files, spec_errors = _real_files(spec_root)
    evidence_files, evidence_errors = _real_files(evidence_root)
    errors = [
        *spec_errors,
        *evidence_errors,
        *_receipt_binding_errors(receipt_path, spec_root),
    ]
    if errors:
        return _blocked(root, identifier, errors)
    archive_date = datetime.fromtimestamp(
        receipt_path.stat().st_mtime, tz=UTC
    ).date().isoformat()
    destination = root / ".divan" / "archive" / f"{archive_date}-{identifier}"
    if destination.exists() or destination.is_symlink():
        return _blocked(root, identifier, ["goal archive destination exists"])
    entries: list[dict[str, str]] = []
    for source_root, prefix, paths in (
        (spec_root, "specs", spec_files),
        (evidence_root, "evidence", evidence_files),
    ):
        for path in paths:
            content = path.read_bytes()
            entries.append(
                {
                    "source": path.relative_to(root).as_posix(),
                    "destination": (
                        pathlib.PurePosixPath(prefix)
                        / path.relative_to(source_root).as_posix()
                    ).as_posix(),
                    "sha256": _sha256(content),
                }
            )
    entries.sort(key=lambda row: row["destination"])
    receipt_entry = next(
        row
        for row in entries
        if row["destination"] == "evidence/receipt.json"
    )
    archive = {
        "schema_version": 1,
        "goal_id": identifier,
        "terminal_state": state,
        "archive_date": archive_date,
        "receipt_sha256": receipt_entry["sha256"],
        "artifacts": {
            row["destination"]: row["sha256"] for row in entries
        },
    }
    value = {
        "schema_version": 1,
        "operation": "goal-archive",
        "status": "PLANNED",
        "project": str(root),
        "goal_id": identifier,
        "destination": destination.relative_to(root).as_posix(),
        "entries": entries,
        "archive": archive,
        "execute_required": True,
    }
    value["plan_digest"] = _plan_digest(value)
    return value


def _safe_remove_empty_tree(root: pathlib.Path) -> None:
    directories = sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        if directory.is_symlink():
            raise ValueError("archive source directory became unsafe")
        directory.rmdir()
    root.rmdir()


def _remove_known_sources(
    root: pathlib.Path, entries: list[dict[str, str]], identifier: str
) -> None:
    for row in entries:
        path = project_os._safe_destination(root, row["source"])
        if path.is_symlink() or not path.is_file():
            raise ValueError("archive source changed before removal")
        if _sha256(path.read_bytes()) != row["sha256"]:
            raise ValueError("archive source hash changed before removal")
        path.unlink()
    spec_root, evidence_root, _receipt = goals._goal_paths(root, identifier)
    _safe_remove_empty_tree(spec_root)
    _safe_remove_empty_tree(evidence_root)


def _remove_archive_tree(root: pathlib.Path) -> None:
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.as_posix(),
        reverse=True,
    ):
        path.unlink()
    _safe_remove_empty_tree(root)


def apply_archive_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Revalidate, stage, and move a goal archive with rollback on failure."""
    if not isinstance(plan, dict) or plan.get("status") != "PLANNED":
        raise ValueError("goal archive plan is invalid or blocked")
    unsigned = {key: value for key, value in plan.items() if key != "plan_digest"}
    if plan.get("plan_digest") != _plan_digest(unsigned):
        raise ValueError("goal archive plan digest changed")
    root = pathlib.Path(str(plan.get("project"))).resolve()
    fresh = build_archive_plan(root, str(plan.get("goal_id")))
    if fresh.get("plan_digest") != plan.get("plan_digest"):
        raise ValueError("goal changed after archive plan")
    destination = project_os._safe_destination(root, plan["destination"])
    staging = destination.parent / (
        f".staging-{plan['goal_id']}-{plan['plan_digest'][7:19]}"
    )
    if staging.exists() or staging.is_symlink():
        raise ValueError("goal archive staging path already exists")
    staging.mkdir(parents=True)
    try:
        for row in plan["entries"]:
            source = project_os._safe_destination(root, row["source"])
            content = source.read_bytes()
            if _sha256(content) != row["sha256"]:
                raise ValueError("goal changed while staging archive")
            target = staging / pathlib.PurePosixPath(row["destination"])
            project_os._atomic_replace(target, content)
        project_os._atomic_replace(
            staging / "archive.json", _canonical_bytes(plan["archive"])
        )
        os.replace(staging, destination)
        try:
            _remove_known_sources(root, plan["entries"], plan["goal_id"])
        except BaseException:
            for row in plan["entries"]:
                source = project_os._safe_destination(root, row["source"])
                if not source.exists():
                    archived = destination / pathlib.PurePosixPath(
                        row["destination"]
                    )
                    project_os._atomic_replace(source, archived.read_bytes())
            _remove_archive_tree(destination)
            raise
    except BaseException:
        if staging.exists() and not staging.is_symlink():
            _remove_archive_tree(staging)
        raise
    return {
        "schema_version": 1,
        "operation": "goal-archive",
        "status": "ARCHIVED",
        "project": root.name,
        "goal_id": plan["goal_id"],
        "archive": plan["destination"],
    }
