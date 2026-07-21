#!/usr/bin/env python3
"""Build Divan's deterministic SPDX 2.3 release SBOM."""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import subprocess
from typing import Any

DOCUMENT_ID = "SPDXRef-DOCUMENT"
EXPECTED_PACKAGES = {
    "core-pack",
    "react-pack",
    "sadrazam",
    "ui-pack",
    "zanaat-pack",
}
LICENSE_ORDER = ("Apache-2.0", "MIT", "CC0-1.0")
SPDX_LICENSES = set(LICENSE_ORDER)
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON nesne olmali: {path.name}")
    return value


def _marketplace_packages(root: pathlib.Path) -> list[dict[str, Any]]:
    claude = _read_json(root / ".claude-plugin" / "marketplace.json")["plugins"]
    codex = _read_json(root / ".agents" / "plugins" / "marketplace.json")["plugins"]
    if not isinstance(claude, list) or not isinstance(codex, list):
        raise ValueError("Marketplace plugins alanlari liste olmali")
    claude_versions = {item["name"]: item["version"] for item in claude}
    codex_versions = {item["name"]: item["version"] for item in codex}
    if claude_versions != codex_versions or set(claude_versions) != EXPECTED_PACKAGES:
        raise ValueError("Claude ve Codex marketplace paketleri birebir eslesmeli")
    return sorted(codex, key=lambda item: item["name"])


def _plugin_licenses(root: pathlib.Path, package: str) -> set[str]:
    manifest = _read_json(root / "plugins" / package / ".claude-plugin" / "plugin.json")
    declared = str(manifest.get("license", ""))
    return {license_id for license_id in SPDX_LICENSES if license_id in declared}


def _third_party_inventory(
    root: pathlib.Path,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    licenses: dict[str, set[str]] = {name: set() for name in EXPECTED_PACKAGES}
    repositories: dict[str, set[str]] = {name: set() for name in EXPECTED_PACKAGES}
    text = (root / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        package = next((name for name in EXPECTED_PACKAGES if cells[0].startswith(name)), None)
        if package is None:
            continue
        licenses[package].update(
            license_id for license_id in SPDX_LICENSES if license_id in cells[3]
        )
        match = re.search(r"github\.com/([^\s|`]+)", cells[2])
        if match:
            repositories[package].add(match.group(1).rstrip("/"))
    return licenses, repositories


def _upstream_heads(root: pathlib.Path) -> dict[str, str]:
    registry = _read_json(root / "registry" / "upstream-baselines.json")
    sources = registry.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Upstream sources alani liste olmali")
    heads = {str(item["repository"]): str(item["reviewed_head"]) for item in sources}
    if any(SHA_PATTERN.fullmatch(head) is None for head in heads.values()):
        raise ValueError("Upstream reviewed_head tam Git SHA olmali")
    return heads


def _license_expression(licenses: set[str], package: str) -> str:
    if not licenses:
        raise ValueError(f"SPDX lisansi bulunamadi: {package}")
    return " AND ".join(item for item in LICENSE_ORDER if item in licenses)


def _source_info(
    repositories: set[str], upstream_heads: dict[str, str]
) -> str:
    missing = sorted(repositories - upstream_heads.keys())
    if missing:
        raise ValueError("kanonik pin yok: " + ", ".join(missing))
    pinned = [
        f"{repository}@{upstream_heads[repository]}"
        for repository in sorted(repositories)
    ]
    origin = ", ".join(pinned) if pinned else "original Divan work"
    return (
        f"Sources: {origin}. Provenance inventory: THIRD_PARTY_LICENSES.md and "
        "registry/upstream-baselines.json."
    )


def _commit_created(root: pathlib.Path, source_commit: str) -> str:
    try:
        value = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "show",
                "--no-patch",
                "--format=%cI",
                f"{source_commit}^{{commit}}",
            ],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        created = datetime.datetime.fromisoformat(value)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise ValueError(f"Git commit bulunamadi veya zamani gecersiz: {source_commit}") from exc
    if created.tzinfo is None:
        raise ValueError(f"Git commit zamani UTC ofseti icermiyor: {source_commit}")
    return created.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _package(
    root: pathlib.Path,
    manifest: dict[str, Any],
    repository: str,
    source_commit: str,
    inventory_licenses: dict[str, set[str]],
    inventory_repositories: dict[str, set[str]],
    upstream_heads: dict[str, str],
) -> dict[str, Any]:
    name = str(manifest["name"])
    version = str(manifest["version"])
    licenses = _plugin_licenses(root, name) | inventory_licenses[name]
    expression = _license_expression(licenses, name)
    return {
        "SPDXID": f"SPDXRef-Package-{name}",
        "name": name,
        "versionInfo": version,
        "downloadLocation": (
            f"https://github.com/{repository}/tree/{source_commit}/plugins/{name}"
        ),
        "filesAnalyzed": False,
        "licenseConcluded": expression,
        "licenseDeclared": expression,
        "copyrightText": "NOASSERTION",
        "supplier": "Organization: Divan",
        "sourceInfo": _source_info(inventory_repositories[name], upstream_heads),
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:generic/divan-{name}@{version}",
            }
        ],
    }


def build_spdx(root: pathlib.Path, version: str, source_commit: str) -> dict[str, Any]:
    """Return a deterministic SPDX 2.3 document for the five Divan packages."""
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError("Surum X.Y.Z biciminde olmali")
    if SHA_PATTERN.fullmatch(source_commit) is None:
        raise ValueError("source_commit 40 karakterlik kucuk harfli Git SHA olmali")
    root = root.resolve()
    release = _read_json(root / "release-manifest.json")
    repository = str(release.get("repository", ""))
    if repository != "trugurpala/divan":
        raise ValueError("release-manifest repository trugurpala/divan olmali")
    inventory_licenses, inventory_repositories = _third_party_inventory(root)
    upstream_heads = _upstream_heads(root)
    packages = [
        _package(
            root,
            manifest,
            repository,
            source_commit,
            inventory_licenses,
            inventory_repositories,
            upstream_heads,
        )
        for manifest in _marketplace_packages(root)
    ]
    described = [package["SPDXID"] for package in packages]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": DOCUMENT_ID,
        "name": f"Divan-v{version}",
        "documentNamespace": (
            f"https://spdx.org/spdxdocs/divan-{version}-{source_commit}"
        ),
        "creationInfo": {
            "created": _commit_created(root, source_commit),
            "creators": ["Organization: Divan (Mühürdar)"],
            "comment": "Timestamp is the immutable source commit time normalized to UTC.",
        },
        "documentDescribes": described,
        "packages": packages,
        "relationships": [
            {
                "spdxElementId": DOCUMENT_ID,
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": package_id,
            }
            for package_id in described
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).parents[1])
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--source-commit", required=True)
    arguments = parser.parse_args()
    version = (arguments.root / "VERSION").read_text(encoding="utf-8").strip()
    document = build_spdx(arguments.root, version, arguments.source_commit)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
