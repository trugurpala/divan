"""Checksum and embedded-source verification for the portable project runner."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import zipfile
from typing import Any

from . import project_state

SOURCE_MEMBER = "divan_runtime/divan-project-source.json"
SOURCE_KEYS = frozenset(
    {
        "schema_version",
        "source_commit",
        "source_ref",
        "source_repository",
        "version",
    }
)
CHECKSUM = re.compile(r"^(?P<digest>[0-9a-f]{64})  (?P<name>[^/\r\n]+)\n$")


def _safe_file(path: pathlib.Path, label: str, maximum: int) -> pathlib.Path:
    if project_state._is_reparse_or_symlink(path):
        raise ValueError(f"{label} uses a symlink or reparse point")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} is unavailable: {error}") from error
    if not resolved.is_file() or resolved.stat().st_size > maximum:
        raise ValueError(f"{label} is unavailable or too large")
    return resolved


def _embedded_source(path: pathlib.Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.namelist().count(SOURCE_MEMBER) != 1:
                raise ValueError("project runner has no unique source identity")
            info = archive.getinfo(SOURCE_MEMBER)
            if info.file_size > 4096:
                raise ValueError("project runner source identity is too large")
            value = json.loads(archive.read(info).decode("utf-8"))
    except (OSError, UnicodeError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        raise ValueError(f"project runner source identity is invalid: {error}") from error
    if not isinstance(value, dict) or set(value) != SOURCE_KEYS:
        raise ValueError("project runner source identity keys are invalid")
    return value


def _verify_checksum(path: pathlib.Path, digest: str) -> None:
    checksum_path = _safe_file(
        path.with_name(path.name + ".sha256"),
        "project runner checksum",
        256,
    )
    try:
        text = checksum_path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"project runner checksum is invalid: {error}") from error
    match = CHECKSUM.fullmatch(text)
    if (
        match is None
        or match.group("name") != path.name
        or match.group("digest") != digest
    ):
        raise ValueError("project runner checksum does not match")


def verify(
    path: pathlib.Path | str, installed_source: dict[str, Any]
) -> tuple[pathlib.Path, str]:
    """Return the resolved runner and checksum after strict offline validation."""
    resolved = _safe_file(pathlib.Path(path), "Divan project runner", 64 * 1024 * 1024)
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    _verify_checksum(resolved, digest)
    embedded = _embedded_source(resolved)
    expected = {"schema_version": 2, **installed_source}
    if embedded != expected:
        raise ValueError("project runner source identity does not match installation")
    return resolved, f"sha256:{digest}"
