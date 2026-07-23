from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "registry" / "forge" / "sources.json"
SHA256_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

ALLOWED_KINDS = {
    "application-generator",
    "application-starter",
    "compatibility-reference",
    "product-base",
    "tool-provider",
}
ALLOWED_STATUSES = {"CANDIDATE", "LOCKED", "REFERENCE"}
ALLOWED_DECISIONS = {"ALTERNATIVE", "GOLDEN_PATH", "PRODUCT_BASE", "REFERENCE", "TOOL"}
ALLOWED_BUILD_EVIDENCE = {"not_applicable", "not_run", "verified"}
ALLOWED_MATERIALIZATION = {
    "composer-project",
    "cookiecutter",
    "copier-or-template-clone",
    "none",
    "official-generator",
    "official-template",
    "official-tool-install",
    "product-fork",
    "service-integration-or-product-fork",
    "template-clone",
    "template-generator",
}


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_errors(source: object, index: int) -> list[str]:
    prefix = f"sources[{index}]"
    if not isinstance(source, dict):
        return [f"{prefix} must be an object"]

    errors: list[str] = []
    required_strings = ("id", "name", "repository", "reviewed_head", "kind", "status")
    for field in required_strings:
        if not isinstance(source.get(field), str) or not source[field].strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")

    repository = source.get("repository")
    if isinstance(repository, str) and not REPOSITORY_RE.fullmatch(repository):
        errors.append(f"{prefix}.repository must use owner/name form")

    reviewed_head = source.get("reviewed_head")
    if isinstance(reviewed_head, str) and not SHA256_RE.fullmatch(reviewed_head):
        errors.append(f"{prefix}.reviewed_head must be a full lowercase commit SHA")

    if source.get("kind") not in ALLOWED_KINDS:
        errors.append(f"{prefix}.kind is unsupported")
    if source.get("status") not in ALLOWED_STATUSES:
        errors.append(f"{prefix}.status is unsupported")
    if source.get("decision") not in ALLOWED_DECISIONS:
        errors.append(f"{prefix}.decision is unsupported")
    if source.get("materialization") not in ALLOWED_MATERIALIZATION:
        errors.append(f"{prefix}.materialization is unsupported")
    if source.get("build_evidence") not in ALLOWED_BUILD_EVIDENCE:
        errors.append(f"{prefix}.build_evidence is unsupported")
    if source.get("auto_install") is not False:
        errors.append(f"{prefix}.auto_install must remain false")

    wave = source.get("wave")
    if not isinstance(wave, int) or wave < 0 or wave > 3:
        errors.append(f"{prefix}.wave must be an integer from 0 to 3")

    license_data = source.get("license")
    if not isinstance(license_data, dict):
        errors.append(f"{prefix}.license must be an object")
    else:
        for field in ("spdx", "evidence_path", "evidence_blob_sha", "scope_note"):
            value = license_data.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.license.{field} must be a non-empty string")
        blob_sha = license_data.get("evidence_blob_sha")
        if isinstance(blob_sha, str) and not SHA256_RE.fullmatch(blob_sha):
            errors.append(f"{prefix}.license.evidence_blob_sha must be a full blob SHA")

    decision = source.get("decision")
    materialization = source.get("materialization")
    profile = source.get("profile")
    if decision in {"GOLDEN_PATH", "ALTERNATIVE", "PRODUCT_BASE"}:
        if not isinstance(profile, str) or not profile.strip():
            errors.append(f"{prefix}.profile is required for materializable sources")
    if decision == "REFERENCE" and materialization != "none":
        errors.append(f"{prefix}.reference sources must not materialize")
    if decision == "TOOL" and source.get("kind") != "tool-provider":
        errors.append(f"{prefix}.TOOL decision requires tool-provider kind")

    return errors


def registry_errors(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["registry root must be an object"]

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("autonomy") != "never-auto-install":
        errors.append("autonomy must remain never-auto-install")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        if policy.get("vendor_source_into_divan") is not False:
            errors.append("policy.vendor_source_into_divan must remain false")
        if policy.get("floating_refs_allowed") is not False:
            errors.append("policy.floating_refs_allowed must remain false")
        if policy.get("unknown_project_mcp_auto_approval") is not False:
            errors.append("policy.unknown_project_mcp_auto_approval must remain false")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return [*errors, "sources must be a non-empty list"]

    ids: set[str] = set()
    repositories: set[str] = set()
    for index, source in enumerate(sources):
        errors.extend(_source_errors(source, index))
        if not isinstance(source, dict):
            continue
        source_id = source.get("id")
        repository = source.get("repository")
        if isinstance(source_id, str):
            if source_id in ids:
                errors.append(f"duplicate source id: {source_id}")
            ids.add(source_id)
        if isinstance(repository, str):
            if repository in repositories:
                errors.append(f"duplicate repository: {repository}")
            repositories.add(repository)

    return errors


def main() -> int:
    errors = registry_errors(load_registry())
    if errors:
        print("Forge registry: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Forge registry: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
