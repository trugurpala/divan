#!/usr/bin/env python3
"""Digest and transactionally quarantine legacy loose Divan skill installs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import shutil
import sys
import uuid
from datetime import UTC, datetime
from typing import Any


class LegacyStateError(RuntimeError):
    """Raised before unsafe legacy state can be changed."""


def tree_digest(root: pathlib.Path) -> str:
    """Return a deterministic digest of a directory without following symlinks."""
    root = root.resolve()
    if not root.is_dir():
        raise LegacyStateError(f"skill directory is missing: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            raise LegacyStateError(f"symlink is not allowed in installed skill: {path}")
        if path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
            continue
        if not path.is_file():
            raise LegacyStateError(f"unsupported filesystem entry: {path}")
        digest.update(b"F\0" + relative + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _resolve_child(path: str, parent: pathlib.Path, label: str) -> pathlib.Path:
    candidate = pathlib.Path(path).resolve()
    if candidate.parent != parent or not candidate.name:
        raise LegacyStateError(f"{label} is outside the skill directory: {candidate}")
    return candidate


def _read_rows(
    manifest: pathlib.Path,
    skills_dir: pathlib.Path,
    state_dir: pathlib.Path,
) -> list[dict[str, Any]]:
    try:
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except OSError as exc:
        raise LegacyStateError(f"manifest is unreadable: {manifest}") from exc
    required = {"skill", "hedef", "yedek", "installed_sha256"}
    if not rows or not required.issubset(rows[0]):
        raise LegacyStateError(
            "manifest lacks per-skill installed_sha256 ownership evidence"
        )

    skills_root = skills_dir.resolve()
    backup_root = (state_dir / "divan-backups").resolve()
    seen: set[pathlib.Path] = set()
    verified: list[dict[str, Any]] = []
    for row in rows:
        name = row.get("skill", "")
        target = _resolve_child(row.get("hedef", ""), skills_root, "recorded target")
        if target.name != name or target in seen:
            raise LegacyStateError(f"invalid or duplicate skill identity: {name}")
        seen.add(target)
        expected = row.get("installed_sha256", "").lower()
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            raise LegacyStateError(f"invalid installed digest for {name}")
        backup_text = row.get("yedek", "")
        backup = pathlib.Path(backup_text).resolve() if backup_text else None
        if backup is not None and not backup.is_relative_to(backup_root):
            raise LegacyStateError(f"recorded backup is outside Divan state: {backup}")
        if target.exists():
            actual = tree_digest(target)
            if actual != expected:
                raise LegacyStateError(
                    f"installed skill changed since setup; refusing to replace: {name}"
                )
        verified.append({"name": name, "target": target, "backup": backup})
    return verified


def _persist(path: pathlib.Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _load_journal(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LegacyStateError(f"legacy journal is unreadable: {path}") from exc
    if not isinstance(value, dict) or value.get("schema") != 1:
        raise LegacyStateError("unsupported legacy journal schema")
    return value


def recover_legacy(journal: pathlib.Path) -> dict[str, Any]:
    """Idempotently reverse a partially completed migration or fallback install."""
    record = _load_journal(journal)
    if record.get("status") == "recovered":
        return record
    status = record.get("status")
    recoverable = status in {
        "in-progress",
        "rolling-back",
        "rollback-incomplete",
    } or (status == "quarantined" and record.get("kind") == "migration")
    if not recoverable:
        raise LegacyStateError(f"legacy journal is not recoverable: {status}")
    operations = record.get("operations")
    if not isinstance(operations, list):
        raise LegacyStateError("legacy journal lacks operations")
    record["status"] = "rolling-back"
    _persist(journal, record)
    try:
        for operation in reversed(operations):
            if not isinstance(operation, dict):
                raise LegacyStateError("legacy journal has an invalid operation")
            target = pathlib.Path(operation["target"])
            backup_text = operation.get("backup")
            backup = pathlib.Path(backup_text) if backup_text else None
            owned = pathlib.Path(operation["owned"])
            kind = record.get("kind")
            if kind == "migration":
                pending = record.get("pending")
                pending_kind = (
                    pending.get("kind")
                    if isinstance(pending, dict)
                    and pending.get("name") == operation.get("name")
                    else None
                )
                quarantined = operation.get("quarantined") is True
                if pending_kind == "quarantine-installed" and owned.exists():
                    quarantined = True
                backup_restored = operation.get("backup_restored") is True
                if (
                    pending_kind == "restore-backup"
                    and backup is not None
                    and not backup.exists()
                    and target.exists()
                ):
                    backup_restored = True
                if backup_restored:
                    if backup is None:
                        raise LegacyStateError("migration journal lost its backup path")
                    if not backup.exists():
                        if not target.exists():
                            raise LegacyStateError(
                                f"recovery cannot locate restored backup: {target}"
                            )
                        record["pending"] = {
                            "kind": "restore-backup-path",
                            "name": operation["name"],
                        }
                        _persist(journal, record)
                        backup.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(backup))
                    operation["backup_restored"] = False
                    record["pending"] = None
                    _persist(journal, record)
                if quarantined:
                    if owned.exists():
                        if target.exists():
                            raise LegacyStateError(
                                f"recovery target is unexpectedly occupied: {target}"
                            )
                        record["pending"] = {
                            "kind": "restore-installed",
                            "name": operation["name"],
                        }
                        _persist(journal, record)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(owned), str(target))
                    operation["quarantined"] = False
                    record["pending"] = None
                    _persist(journal, record)
            elif kind == "install":
                if backup is not None and backup.exists():
                    if target.exists():
                        if tree_digest(target) != operation["installed_sha256"]:
                            raise LegacyStateError(
                                f"changed fallback target blocks recovery: {target}"
                            )
                        owned.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(owned))
                    record["pending"] = {"kind": "restore-collision", "name": operation["name"]}
                    _persist(journal, record)
                    shutil.move(str(backup), str(target))
                elif target.exists() and operation.get("had_target") is False:
                    if tree_digest(target) != operation["installed_sha256"]:
                        raise LegacyStateError(
                            f"changed fallback target blocks recovery: {target}"
                        )
                    owned.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(target), str(owned))
            else:
                raise LegacyStateError(f"unknown legacy journal kind: {kind}")
            operation["recovered"] = True
            record["pending"] = None
            _persist(journal, record)
    except BaseException as exc:
        record["status"] = "rollback-incomplete"
        record["error"] = str(exc)
        _persist(journal, record)
        if isinstance(exc, LegacyStateError):
            raise
        raise LegacyStateError(f"legacy recovery is incomplete: {exc}") from exc
    record["status"] = "recovered"
    record["pending"] = None
    record["recovered_at"] = datetime.now(UTC).isoformat()
    _persist(journal, record)
    return record


def migrate_legacy(
    manifest: pathlib.Path,
    skills_dir: pathlib.Path,
    state_dir: pathlib.Path,
    *,
    fail_after: int | None = None,
    journal_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Preflight all rows, then quarantine atomically or restore every move."""
    rows = _read_rows(manifest.resolve(), skills_dir, state_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    quarantine = state_dir.resolve() / "divan-quarantine" / f"{stamp}-{uuid.uuid4().hex[:8]}"
    journal = journal_path or (
        state_dir.resolve()
        / "divan-transactions"
        / f"legacy-migrate-{stamp}-{uuid.uuid4().hex[:8]}.json"
    )
    operations = [
        {
            "name": row["name"],
            "target": str(row["target"]),
            "backup": str(row["backup"]) if row["backup"] is not None else "",
            "owned": str(quarantine / row["name"]),
            "quarantined": False,
            "backup_restored": False,
            "recovered": False,
        }
        for row in rows
    ]
    record: dict[str, Any] = {
        "schema": 1,
        "kind": "migration",
        "status": "in-progress",
        "manifest": str(manifest.resolve()),
        "skills_dir": str(skills_dir.resolve()),
        "state_dir": str(state_dir.resolve()),
        "journal": str(journal),
        "quarantine": str(quarantine),
        "operations": operations,
        "pending": None,
    }
    _persist(journal, record)
    try:
        for index, operation in enumerate(operations, start=1):
            target = pathlib.Path(operation["target"])
            backup = pathlib.Path(operation["backup"]) if operation["backup"] else None
            quarantined = pathlib.Path(operation["owned"])
            if target.exists():
                record["pending"] = {"kind": "quarantine-installed", "name": operation["name"]}
                _persist(journal, record)
                quarantined.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(quarantined))
                operation["quarantined"] = True
                record["pending"] = None
                _persist(journal, record)
            if backup is not None and backup.exists():
                record["pending"] = {"kind": "restore-backup", "name": operation["name"]}
                _persist(journal, record)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(target))
                operation["backup_restored"] = True
                record["pending"] = None
                _persist(journal, record)
            if fail_after is not None and index == fail_after:
                raise OSError("fixture failure after row mutation")
    except BaseException as exc:
        recover_legacy(journal)
        raise LegacyStateError(f"legacy migration failed and was rolled back: {exc}") from exc

    record["status"] = "quarantined"
    record["pending"] = None
    record["finished_at"] = datetime.now(UTC).isoformat()
    _persist(journal, record)
    return {
        "status": "quarantined",
        "manifest": str(manifest.resolve()),
        "quarantine": str(quarantine),
        "journal": str(journal),
        "skill_count": len(rows),
    }


def install_legacy(
    source: pathlib.Path,
    skills_dir: pathlib.Path,
    state_dir: pathlib.Path,
    metadata: dict[str, str],
    *,
    fail_after: int | None = None,
    journal_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Stage every loose skill, then install all rows with durable rollback state."""
    source = source.resolve()
    skills_dir = skills_dir.resolve()
    state_dir = state_dir.resolve()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    identifier = f"{stamp}-{uuid.uuid4().hex[:8]}"
    staging = state_dir / "divan-staging" / identifier
    rollback_owned = state_dir / "divan-quarantine" / f"failed-install-{identifier}"
    backup_root = state_dir / "divan-backups" / identifier
    journal = journal_path or state_dir / "divan-transactions" / f"legacy-install-{identifier}.json"
    manifest = state_dir / f"divan-install-{identifier}.tsv"

    candidates = sorted((source / "plugins").glob("*/skills/*"))
    candidates = [path for path in candidates if (path / "SKILL.md").is_file()]
    if not candidates:
        raise LegacyStateError("no installable skills found")
    names = [path.name for path in candidates]
    if len(names) != len(set(names)):
        raise LegacyStateError("duplicate skill name in source")
    staging.mkdir(parents=True, exist_ok=False)
    operations: list[dict[str, Any]] = []
    for candidate in candidates:
        staged = staging / candidate.name
        shutil.copytree(candidate, staged)
        target = skills_dir / candidate.name
        operations.append(
            {
                "name": candidate.name,
                "target": str(target),
                "backup": str(backup_root / candidate.name) if target.exists() else "",
                "owned": str(rollback_owned / candidate.name),
                "staged": str(staged),
                "had_target": target.exists(),
                "installed_sha256": tree_digest(staged),
                "recovered": False,
            }
        )
    record: dict[str, Any] = {
        "schema": 1,
        "kind": "install",
        "status": "in-progress",
        "journal": str(journal),
        "manifest": str(manifest),
        "skills_dir": str(skills_dir),
        "state_dir": str(state_dir),
        "operations": operations,
        "pending": None,
    }
    _persist(journal, record)
    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
        for index, operation in enumerate(operations, start=1):
            target = pathlib.Path(operation["target"])
            backup = pathlib.Path(operation["backup"]) if operation["backup"] else None
            staged = pathlib.Path(operation["staged"])
            if target.exists():
                if backup is None:
                    raise LegacyStateError(f"unowned target appeared during install: {target}")
                record["pending"] = {"kind": "backup-collision", "name": operation["name"]}
                _persist(journal, record)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(backup))
                record["pending"] = None
                _persist(journal, record)
            record["pending"] = {"kind": "install-staged", "name": operation["name"]}
            _persist(journal, record)
            shutil.move(str(staged), str(target))
            record["pending"] = None
            _persist(journal, record)
            if fail_after is not None and index == fail_after:
                raise OSError("fixture failure after fallback install row")
    except BaseException as exc:
        recover_legacy(journal)
        raise LegacyStateError(f"fallback install failed and was rolled back: {exc}") from exc

    fieldnames = (
        "skill",
        "hedef",
        "yedek",
        "surum",
        "ref",
        "source_commit",
        "archive_sha256",
        "installed_sha256",
        "installed_at",
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for operation in operations:
            writer.writerow(
                {
                    "skill": operation["name"],
                    "hedef": operation["target"],
                    "yedek": operation["backup"],
                    "surum": metadata["version"],
                    "ref": metadata["ref"],
                    "source_commit": metadata["source_commit"],
                    "archive_sha256": metadata["archive_sha256"],
                    "installed_sha256": operation["installed_sha256"],
                    "installed_at": metadata["installed_at"],
                }
            )
    (state_dir / "divan-install-latest").write_text(str(manifest) + "\n", encoding="utf-8")
    record["status"] = "installed"
    record["finished_at"] = datetime.now(UTC).isoformat()
    _persist(journal, record)
    return {
        "status": "installed",
        "manifest": str(manifest),
        "journal": str(journal),
        "skill_count": len(operations),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    digest_parser = subparsers.add_parser("digest")
    digest_parser.add_argument("path", type=pathlib.Path)
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    migrate_parser.add_argument("--skills-dir", type=pathlib.Path, required=True)
    migrate_parser.add_argument("--state-dir", type=pathlib.Path, required=True)
    migrate_parser.add_argument("--journal", type=pathlib.Path)
    recover_parser = subparsers.add_parser("recover")
    recover_parser.add_argument("--journal", type=pathlib.Path, required=True)
    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("--source", type=pathlib.Path, required=True)
    install_parser.add_argument("--skills-dir", type=pathlib.Path, required=True)
    install_parser.add_argument("--state-dir", type=pathlib.Path, required=True)
    for field in ("version", "ref", "source-commit", "archive-sha256", "installed-at"):
        install_parser.add_argument(f"--{field}", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            print(tree_digest(args.path))
        elif args.command == "recover":
            print(json.dumps(recover_legacy(args.journal), ensure_ascii=False))
        elif args.command == "install":
            fail_after_text = os.environ.get("DIVAN_TEST_INSTALL_FAIL_AFTER")
            fail_after = int(fail_after_text) if fail_after_text else None
            print(
                json.dumps(
                    install_legacy(
                        args.source,
                        args.skills_dir,
                        args.state_dir,
                        {
                            "version": args.version,
                            "ref": args.ref,
                            "source_commit": args.source_commit,
                            "archive_sha256": args.archive_sha256,
                            "installed_at": args.installed_at,
                        },
                        fail_after=fail_after,
                    ),
                    ensure_ascii=False,
                )
            )
        else:
            fail_after_text = os.environ.get("DIVAN_TEST_FAIL_AFTER")
            fail_after = int(fail_after_text) if fail_after_text else None
            print(
                json.dumps(
                    migrate_legacy(
                        args.manifest,
                        args.skills_dir,
                        args.state_dir,
                        fail_after=fail_after,
                        journal_path=args.journal,
                    ),
                    ensure_ascii=False,
                )
            )
        return 0
    except (LegacyStateError, ValueError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
