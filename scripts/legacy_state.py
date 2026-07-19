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


def migrate_legacy(
    manifest: pathlib.Path,
    skills_dir: pathlib.Path,
    state_dir: pathlib.Path,
    *,
    fail_after: int | None = None,
) -> dict[str, Any]:
    """Preflight all rows, then quarantine atomically or restore every move."""
    rows = _read_rows(manifest.resolve(), skills_dir, state_dir)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    quarantine = state_dir.resolve() / "divan-quarantine" / f"{stamp}-{uuid.uuid4().hex[:8]}"
    operations: list[dict[str, Any]] = []
    try:
        for index, row in enumerate(rows, start=1):
            target: pathlib.Path = row["target"]
            backup: pathlib.Path | None = row["backup"]
            quarantined = quarantine / row["name"]
            operation = {
                **row,
                "quarantined": quarantined,
                "target_moved": False,
                "backup_restored": False,
            }
            operations.append(operation)
            if target.exists():
                quarantined.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(quarantined))
                operation["target_moved"] = True
            if backup is not None and backup.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(target))
                operation["backup_restored"] = True
            if fail_after is not None and index == fail_after:
                raise OSError("fixture failure after row mutation")
    except BaseException as exc:
        rollback_errors: list[str] = []
        for operation in reversed(operations):
            target = operation["target"]
            backup = operation["backup"]
            quarantined = operation["quarantined"]
            try:
                if operation["backup_restored"] and target.exists() and backup is not None:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(target), str(backup))
                if operation["target_moved"] and quarantined.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(quarantined), str(target))
            except OSError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        detail = f"; rollback errors: {' | '.join(rollback_errors)}" if rollback_errors else ""
        raise LegacyStateError(f"legacy migration failed and was rolled back: {exc}{detail}") from exc

    return {
        "status": "quarantined",
        "manifest": str(manifest.resolve()),
        "quarantine": str(quarantine),
        "skill_count": len(rows),
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
    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            print(tree_digest(args.path))
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
