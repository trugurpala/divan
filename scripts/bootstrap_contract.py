"""Fail-closed identity and catalog contract for the standalone bootstrap."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

PACKAGES = {"sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack"}
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
CANONICAL_SOURCE = "https://github.com/trugurpala/divan.git"


class ContractError(ValueError):
    """Raised when bundled bootstrap authority cannot be proven."""


def _read(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"bundled contract is unreadable: {path.name}") from error
    if not isinstance(value, dict):
        raise ContractError(f"bundled contract is invalid: {path.name}")
    return value


def validate(
    identity: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    identity_keys = {
        "schema_version",
        "source_commit",
        "source_ref",
        "source_repository",
        "version",
    }
    catalog_keys = {
        "marketplace_digest",
        "packages",
        "schema_version",
        "skill_count",
        "version",
    }
    if set(identity) != identity_keys or identity.get("schema_version") != 1:
        raise ContractError("bundled identity schema is invalid")
    if set(catalog) != catalog_keys or catalog.get("schema_version") != 1:
        raise ContractError("bundled catalog schema is invalid")
    version = identity.get("version")
    if (
        not isinstance(version, str)
        or SEMVER.fullmatch(version) is None
        or identity.get("source_ref") != f"v{version}"
        or identity.get("source_repository") != CANONICAL_SOURCE
        or SHA40.fullmatch(str(identity.get("source_commit", ""))) is None
        or catalog.get("version") != version
        or SHA256.fullmatch(str(catalog.get("marketplace_digest", ""))) is None
    ):
        raise ContractError("bundled release identity is invalid")
    packages = catalog.get("packages")
    if not isinstance(packages, dict) or set(packages) != PACKAGES:
        raise ContractError("bundled catalog package set is invalid")
    unique: set[str] = set()
    for name, row in packages.items():
        if (
            not isinstance(row, dict)
            or set(row) != {"skills", "version"}
            or not isinstance(row.get("version"), str)
            or SEMVER.fullmatch(row["version"]) is None
            or not isinstance(row.get("skills"), list)
            or not row["skills"]
            or any(not isinstance(skill, str) or not skill for skill in row["skills"])
            or row["skills"] != sorted(row["skills"])
            or len(row["skills"]) != len(set(row["skills"]))
            or unique.intersection(row["skills"])
        ):
            raise ContractError(f"bundled catalog package is invalid: {name}")
        unique.update(row["skills"])
    if catalog.get("skill_count") != 41 or len(unique) != 41:
        raise ContractError("bundled catalog must define 41 unique skills")
    typed_identity = {key: str(identity[key]) for key in identity_keys - {"schema_version"}}
    return typed_identity, packages


def load(root: pathlib.Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]] | None:
    identity_path = root / "divan-bootstrap-source.json"
    catalog_path = root / "divan-bootstrap-catalog.json"
    if not identity_path.exists() and not catalog_path.exists():
        return None
    if not identity_path.is_file() or not catalog_path.is_file():
        raise ContractError("bundled identity and catalog must both exist")
    return validate(_read(identity_path), _read(catalog_path))
