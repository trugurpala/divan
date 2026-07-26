"""Strict ownership state for installed Divan Project OS contracts."""
from __future__ import annotations

import json
import pathlib
import re
import stat
from typing import Any

STATE_KEYS = frozenset(
    {
        "schema_version",
        "product",
        "contract_schema",
        "installed",
        "project_identity",
        "managed_files",
    }
)
SOURCE_KEYS = frozenset(
    {"version", "source_repository", "source_ref", "source_commit"}
)
MANAGED_KEYS = frozenset({"path", "mode", "payload_sha256"})
MODES = frozenset({"whole-file", "marked-block"})
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
IMMUTABLE_REF = re.compile(
    r"^(?:v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"|development@[0-9a-f]{40})$"
)
WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
SOURCE_REPOSITORY = "https://github.com/trugurpala/divan"


def _is_reparse_or_symlink(path: pathlib.Path) -> bool:
    try:
        details = path.lstat()
    except OSError:
        return False
    attributes = getattr(details, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(details.st_mode) or bool(attributes & reparse)


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if WINDOWS_DRIVE.match(value):
        return False
    path = pathlib.PurePosixPath(value)
    return (
        not path.is_absolute()
        and "." not in path.parts
        and ".." not in path.parts
        and path.as_posix() == value
    )


def _source_errors(value: Any) -> list[str]:
    if not isinstance(value, dict) or set(value) != SOURCE_KEYS:
        return ["installed source keys are invalid"]
    errors: list[str] = []
    if not isinstance(value.get("version"), str) or SEMVER.fullmatch(
        value["version"]
    ) is None:
        errors.append("installed version is invalid")
    if value.get("source_repository") != SOURCE_REPOSITORY:
        errors.append("installed source_repository is invalid")
    if not isinstance(value.get("source_ref"), str) or IMMUTABLE_REF.fullmatch(
        value["source_ref"]
    ) is None:
        errors.append("installed source_ref is not immutable")
    if not isinstance(value.get("source_commit"), str) or HEX_40.fullmatch(
        value["source_commit"]
    ) is None:
        errors.append("installed source_commit is invalid")
    return errors


def _managed_errors(value: Any) -> list[str]:
    if not isinstance(value, list):
        return ["managed_files must be an array"]
    errors: list[str] = []
    paths: list[str] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict) or set(row) != MANAGED_KEYS:
            errors.append(f"managed_files[{index}] keys are invalid")
            continue
        path = row.get("path")
        if not _safe_relative_path(path):
            errors.append(f"managed_files[{index}].path is invalid")
        elif isinstance(path, str):
            paths.append(path)
        if row.get("mode") not in MODES:
            errors.append(f"managed_files[{index}].mode is invalid")
        digest = row.get("payload_sha256")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
            errors.append(f"managed_files[{index}].payload_sha256 is invalid")
    if paths != sorted(paths):
        errors.append("managed_files must be sorted by path")
    if len(paths) != len(set(paths)):
        errors.append("managed_files paths must be unique")
    return errors


def validate_install_state(value: Any) -> list[str]:
    """Return deterministic schema errors for an ownership-state value."""
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        return ["install state keys are invalid"]
    errors: list[str] = []
    if value.get("schema_version") != 1:
        errors.append("install state schema_version must be 1")
    if value.get("product") != "divan-project-os":
        errors.append("install state product is invalid")
    if value.get("contract_schema") != 2:
        errors.append("install state contract_schema must be 2")
    errors.extend(_source_errors(value.get("installed")))
    identity = value.get("project_identity")
    if not isinstance(identity, str) or SHA256.fullmatch(identity) is None:
        errors.append("install state project_identity is invalid")
    errors.extend(_managed_errors(value.get("managed_files")))
    return errors


def serialize_install_state(value: dict[str, Any]) -> bytes:
    """Serialize a valid ownership state as canonical UTF-8 JSON."""
    errors = validate_install_state(value)
    if errors:
        raise ValueError("; ".join(errors))
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def load_install_state(
    project: pathlib.Path | str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Load a real, bounded ownership-state file without mutation."""
    root = pathlib.Path(project).resolve()
    path = root / ".divan" / "install-state.json"
    cursor = root
    unsafe = False
    for part in (".divan", "install-state.json"):
        cursor = cursor / part
        unsafe = unsafe or _is_reparse_or_symlink(cursor)
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError:
        unsafe = True
    if unsafe or not path.is_file():
        return None, [".divan/install-state.json is unavailable or unsafe"]
    try:
        if path.stat().st_size > 1024 * 1024:
            return None, [".divan/install-state.json exceeds 1 MiB"]
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [f".divan/install-state.json is invalid: {error}"]
    errors = validate_install_state(value)
    return (value if isinstance(value, dict) else None), errors
