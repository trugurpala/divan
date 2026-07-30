"""Fail-closed identity and catalog contract for the standalone bootstrap."""

from __future__ import annotations

import hashlib
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


def expected_packages(
    root: pathlib.Path, package_names: set[str]
) -> dict[str, dict[str, Any]]:
    """Read either the bundled or native five-package catalog."""
    bundled = load(root)
    if bundled is not None:
        return bundled[1]
    path = root / ".agents" / "plugins" / "marketplace.json"
    marketplace = _read(path)
    expected: dict[str, dict[str, Any]] = {}
    for plugin in marketplace.get("plugins", []):
        if not isinstance(plugin, dict):
            continue
        name, version, source = plugin.get("name"), plugin.get("version"), plugin.get("source")
        if not isinstance(name, str) or not isinstance(version, str) or not isinstance(source, dict):
            continue
        relative = source.get("path")
        if not isinstance(relative, str):
            continue
        skills = sorted(
            item.parent.name
            for item in (root / relative / "skills").glob("*/SKILL.md")
        )
        expected[name] = {"version": version, "skills": skills}
    if set(expected) != package_names:
        raise ContractError("native catalog does not define the expected five packages")
    if len({skill for row in expected.values() for skill in row["skills"]}) != 41:
        raise ContractError("native catalog does not define exactly 41 unique skills")
    return expected


def target_evidence(
    root: pathlib.Path,
    versions: dict[str, str],
) -> dict[str, Any] | None:
    """Return immutable install evidence when the root is a bundled bootstrap."""
    bundled = load(root)
    if bundled is None:
        return None
    identity, _ = bundled
    catalog = _read(root / "divan-bootstrap-catalog.json")
    return {
        "source": identity["source_repository"],
        "ref": identity["source_ref"],
        "root": str(root.resolve()),
        "commit": identity["source_commit"],
        "catalog_digest": catalog["marketplace_digest"],
        "versions": versions,
    }


def fallback_environment(
    options: Any,
    root: pathlib.Path,
    bootstrap: object,
    python: str,
) -> dict[str, str]:
    """Bind a fallback install to an embedded immutable release authority."""
    environment = {"DIVAN_REF": options.ref, "DIVAN_PYTHON": python}
    bundled = load(root)
    if bundled is None:
        return environment
    identity, _ = bundled
    if options.source != identity["source_repository"] or options.ref != identity["source_ref"]:
        raise ContractError("fallback request does not match bundled release authority")
    environment.update(
        {
            "DIVAN_SOURCE_DIR": str(root.resolve()),
            "DIVAN_SOURCE_COMMIT": identity["source_commit"],
        }
    )
    if isinstance(bootstrap, str) and pathlib.Path(bootstrap).is_file():
        digest = hashlib.sha256(pathlib.Path(bootstrap).read_bytes()).hexdigest()
        environment["DIVAN_ARCHIVE_SHA256"] = digest
    return environment
