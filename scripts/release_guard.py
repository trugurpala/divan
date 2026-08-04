#!/usr/bin/env python3
"""Validate GitHub release policy and state before public mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import zipfile
from typing import Any

TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
FIXED_ASSETS = {
    "divan-project.pyz",
    "divan-project.pyz.sha256",
    "divan.pyz",
    "divan.pyz.sha256",
}
SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class ReleaseGuardError(RuntimeError):
    """Raised when GitHub cannot prove a safe release transition."""


def load_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseGuardError(f"GitHub evidence is unreadable: {path}") from exc


def require_immutable_releases(value: Any) -> None:
    """Require GitHub release immutability before creating a public release."""
    if not isinstance(value, dict) or value.get("enabled") is not True:
        raise ReleaseGuardError("GitHub immutable releases are not enabled")


def require_tag_ruleset(value: Any, tag: str) -> None:
    """Require one active, no-bypass update/deletion guard for stable tags."""
    _require_tag(tag)
    if not isinstance(value, dict):
        raise ReleaseGuardError("GitHub tag ruleset evidence is invalid")
    conditions = value.get("conditions")
    refs = conditions.get("ref_name") if isinstance(conditions, dict) else None
    include = refs.get("include") if isinstance(refs, dict) else None
    exclude = refs.get("exclude") if isinstance(refs, dict) else None
    patterns = {"~ALL", "refs/tags/v*", f"refs/tags/{tag}"}
    rules = value.get("rules")
    rule_types = (
        {row.get("type") for row in rules if isinstance(row, dict)}
        if isinstance(rules, list)
        else set()
    )
    valid = (
        value.get("target") == "tag"
        and value.get("enforcement") == "active"
        and value.get("bypass_actors") == []
        and isinstance(include, list)
        and any(pattern in patterns for pattern in include)
        and exclude == []
        and {"update", "deletion"} <= rule_types
    )
    if not valid:
        raise ReleaseGuardError(
            "GitHub tag ruleset does not lock stable tag updates and deletions"
        )


def release_state(value: Any, tag: str) -> str:
    """Return missing or published after validating an exact stable release."""
    _require_tag(tag)
    if not isinstance(value, list) or not all(isinstance(page, list) for page in value):
        raise ReleaseGuardError("GitHub release list evidence is invalid")
    matches = [
        row
        for page in value
        for row in page
        if isinstance(row, dict) and row.get("tag_name") == tag
    ]
    if not matches:
        return "missing"
    if len(matches) != 1:
        raise ReleaseGuardError(f"GitHub has duplicate Release records for {tag}")
    release = matches[0]
    valid = (
        release.get("draft") is False
        and release.get("prerelease") is False
        and release.get("immutable") is True
        and isinstance(release.get("published_at"), str)
        and bool(release["published_at"])
    )
    if not valid:
        raise ReleaseGuardError(f"GitHub Release {tag} is not published and immutable")
    require_exact_assets(release.get("assets"), tag)
    return "published"


def require_exact_assets(value: Any, tag: str) -> None:
    """Require the complete, duplicate-free asset set for one stable release."""
    _require_tag(tag)
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ReleaseGuardError(f"GitHub Release {tag} asset evidence is invalid")
    names = [row.get("name") for row in value]
    expected = FIXED_ASSETS | {
        f"divan-{tag}.zip",
        f"divan-{tag}.sha256",
        f"divan-{tag}.spdx.json",
    }
    if (
        not all(isinstance(name, str) and name for name in names)
        or len(names) != len(set(names))
        or set(names) != expected
    ):
        raise ReleaseGuardError(
            f"GitHub Release {tag} assets do not match the exact release contract"
        )


def require_release_bundle(root: pathlib.Path, tag: str) -> str:
    """Validate the exact cross-job artifact bundle and return its source commit."""
    _require_tag(tag)
    release_assets = FIXED_ASSETS | {
        f"divan-{tag}.zip",
        f"divan-{tag}.sha256",
        f"divan-{tag}.spdx.json",
    }
    expected = release_assets | {"divan-release-notes.md"}
    _require_bundle_entries(root, expected)

    checksum = root / f"divan-{tag}.sha256"
    try:
        lines = checksum.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ReleaseGuardError("release bundle checksum is unreadable") from exc
    hashed_names = (
        f"divan-{tag}.zip",
        f"divan-{tag}.spdx.json",
        "divan-project.pyz",
        "divan-project.pyz.sha256",
        "divan.pyz",
        "divan.pyz.sha256",
    )
    if len(lines) != len(hashed_names) + 2:
        raise ReleaseGuardError("release bundle checksum contract is invalid")
    for line, name in zip(lines[: len(hashed_names)], hashed_names, strict=True):
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match is None or match.group(2) != name:
            raise ReleaseGuardError("release bundle checksum contract is invalid")
        if _sha256_file(root / name) != match.group(1):
            raise ReleaseGuardError(f"release bundle asset digest differs: {name}")

    source_prefix = "source_commit="
    tag_prefix = "tag="
    if not lines[-2].startswith(source_prefix) or lines[-1] != f"{tag_prefix}{tag}":
        raise ReleaseGuardError("release bundle source identity is invalid")
    source_commit = lines[-2].removeprefix(source_prefix)
    if not SOURCE_COMMIT.fullmatch(source_commit):
        raise ReleaseGuardError("release bundle source identity is invalid")
    _require_runner_identity(
        root / "divan.pyz",
        "divan-bootstrap-source.json",
        {
            "schema_version": 1,
            "source_commit": source_commit,
            "source_ref": tag,
            "source_repository": "https://github.com/trugurpala/divan.git",
        },
    )
    _require_runner_identity(
        root / "divan-project.pyz",
        "divan_runtime/divan-project-source.json",
        {
            "schema_version": 2,
            "source_commit": source_commit,
            "source_ref": tag,
            "source_repository": "https://github.com/trugurpala/divan",
        },
    )
    _require_sbom_identity(root / f"divan-{tag}.spdx.json", tag, source_commit)
    return source_commit


def _require_runner_identity(
    path: pathlib.Path,
    member_name: str,
    expected: dict[str, object],
) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            matches = [item for item in archive.infolist() if item.filename == member_name]
            if len(matches) != 1 or matches[0].file_size > 4096:
                raise ReleaseGuardError("release runner embedded source identity is invalid")
            value = json.loads(archive.read(matches[0]))
    except (OSError, KeyError, UnicodeError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise ReleaseGuardError(
            "release runner embedded source identity is unreadable"
        ) from exc
    if value != expected:
        raise ReleaseGuardError("release runner embedded source identity is invalid")


def _require_sbom_identity(path: pathlib.Path, tag: str, source_commit: str) -> None:
    value = load_json(path)
    version = tag.removeprefix("v")
    expected = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"Divan-{tag}",
        "documentNamespace": (
            f"https://spdx.org/spdxdocs/divan-{version}-{source_commit}"
        ),
    }
    if not isinstance(value, dict) or any(value.get(key) != item for key, item in expected.items()):
        raise ReleaseGuardError("release SBOM source identity is invalid")


def _require_bundle_entries(root: pathlib.Path, expected: set[str]) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ReleaseGuardError("release bundle root is not a real directory")
    try:
        entries = list(root.iterdir())
    except OSError as exc:
        raise ReleaseGuardError("release bundle cannot be read") from exc
    if (
        any(entry.is_symlink() or not entry.is_file() for entry in entries)
        or len(entries) != len(expected)
        or {entry.name for entry in entries} != expected
    ):
        raise ReleaseGuardError("release bundle does not match the exact file contract")


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ReleaseGuardError("release bundle asset is unreadable") from exc
    return digest.hexdigest()


def _require_tag(tag: str) -> None:
    if not TAG.fullmatch(tag):
        raise ReleaseGuardError("a stable SemVer release tag is required")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "kind",
        choices=("bundle", "immutable", "ruleset", "releases"),
    )
    parser.add_argument("path", type=pathlib.Path)
    parser.add_argument("--tag")
    options = parser.parse_args()
    try:
        if options.kind == "bundle":
            if options.tag is None:
                raise ReleaseGuardError("--tag is required for a release bundle")
            result = require_release_bundle(options.path, options.tag)
        else:
            value = load_json(options.path)
            if options.kind == "immutable":
                require_immutable_releases(value)
                result = "enabled"
            elif options.kind == "ruleset":
                if options.tag is None:
                    raise ReleaseGuardError("--tag is required for ruleset evidence")
                require_tag_ruleset(value, options.tag)
                result = "protected"
            else:
                if options.tag is None:
                    raise ReleaseGuardError("--tag is required for release evidence")
                result = release_state(value, options.tag)
    except ReleaseGuardError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
