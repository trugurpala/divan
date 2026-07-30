"""Checksum and embedded-source verification for the portable project runner."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
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
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = "https://github.com/trugurpala/divan"
RELEASE_API = "https://api.github.com/repos/trugurpala/divan/releases/tags/"
MAX_RELEASE_RESPONSE = 1024 * 1024


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


def _release_asset_digest(payload: object, installed_source: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("GitHub release authority is invalid")
    assets = payload.get("assets")
    expected_url = (
        f"{REPOSITORY}/releases/download/{installed_source['source_ref']}/"
        "divan-project.pyz"
    )
    matches = [
        row
        for row in assets
        if isinstance(assets, list)
        and isinstance(row, dict)
        and row.get("name") == "divan-project.pyz"
    ] if isinstance(assets, list) else []
    if (
        payload.get("tag_name") != installed_source.get("source_ref")
        or payload.get("draft") is not False
        or len(matches) != 1
        or matches[0].get("browser_download_url") != expected_url
        or SHA256.fullmatch(str(matches[0].get("digest", ""))) is None
    ):
        raise ValueError("GitHub release runner authority does not match")
    return str(matches[0]["digest"])


def github_release_digest(installed_source: dict[str, Any]) -> str:
    """Read the runner digest from the fixed public GitHub Release authority."""
    if installed_source.get("source_repository") != REPOSITORY:
        raise ValueError("installed source repository is not the Divan authority")
    source_ref = str(installed_source.get("source_ref", ""))
    url = RELEASE_API + urllib.parse.quote(source_ref, safe="")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "divan-clean-room-proof",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read(MAX_RELEASE_RESPONSE + 1)
    except (OSError, urllib.error.URLError) as error:
        raise ValueError("GitHub release authority is unavailable") from error
    if len(content) > MAX_RELEASE_RESPONSE:
        raise ValueError("GitHub release authority response is too large")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("GitHub release authority response is invalid") from error
    return _release_asset_digest(payload, installed_source)


def verify(
    path: pathlib.Path | str,
    installed_source: dict[str, Any],
    *,
    expected_digest: str | None = None,
) -> tuple[pathlib.Path, str]:
    """Validate the runner against local integrity and public release authority."""
    resolved = _safe_file(pathlib.Path(path), "Divan project runner", 64 * 1024 * 1024)
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    _verify_checksum(resolved, digest)
    authority_digest = (
        github_release_digest(installed_source)
        if expected_digest is None
        else expected_digest
    )
    if (
        SHA256.fullmatch(str(authority_digest)) is None
        or authority_digest != f"sha256:{digest}"
    ):
        raise ValueError("project runner does not match GitHub release authority")
    embedded = _embedded_source(resolved)
    expected = {"schema_version": 2, **installed_source}
    if embedded != expected:
        raise ValueError("project runner source identity does not match installation")
    return resolved, authority_digest
