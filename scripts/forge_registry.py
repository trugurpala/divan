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
MATERIALIZABLE_DECISIONS = {"ALTERNATIVE", "GOLDEN_PATH", "PRODUCT_BASE"}
REQUIRED_SOURCE_STRINGS = ("id", "name", "repository", "reviewed_head", "kind", "status")
REQUIRED_LICENSE_STRINGS = ("spdx", "evidence_path", "evidence_blob_sha", "scope_note")


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _required_string_errors(source: dict[str, Any], prefix: str) -> list[str]:
    return [
        f"{prefix}.{field} must be a non-empty string"
        for field in REQUIRED_SOURCE_STRINGS
        if not isinstance(source.get(field), str) or not source.get(field, "").strip()
    ]


def _identity_errors(source: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    repository = source.get("repository")
    reviewed_head = source.get("reviewed_head")
    if isinstance(repository, str) and not REPOSITORY_RE.fullmatch(repository):
        errors.append(f"{prefix}.repository must use owner/name form")
    if isinstance(reviewed_head, str) and not SHA256_RE.fullmatch(reviewed_head):
        errors.append(f"{prefix}.reviewed_head must be a full lowercase commit SHA")
    return errors


def _enum_errors(source: dict[str, Any], prefix: str) -> list[str]:
    checks = (
        ("kind", ALLOWED_KINDS),
        ("status", ALLOWED_STATUSES),
        ("decision", ALLOWED_DECISIONS),
        ("materialization", ALLOWED_MATERIALIZATION),
        ("build_evidence", ALLOWED_BUILD_EVIDENCE),
    )
    return [f"{prefix}.{field} is unsupported" for field, allowed in checks if source.get(field) not in allowed]


def _safety_errors(source: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    if source.get("auto_install") is not False:
        errors.append(f"{prefix}.auto_install must remain false")
    wave = source.get("wave")
    if not isinstance(wave, int) or isinstance(wave, bool) or not 0 <= wave <= 3:
        errors.append(f"{prefix}.wave must be an integer from 0 to 3")
    return errors


def _license_errors(source: dict[str, Any], prefix: str) -> list[str]:
    license_data = source.get("license")
    if not isinstance(license_data, dict):
        return [f"{prefix}.license must be an object"]
    errors = [
        f"{prefix}.license.{field} must be a non-empty string"
        for field in REQUIRED_LICENSE_STRINGS
        if not isinstance(license_data.get(field), str) or not license_data.get(field, "").strip()
    ]
    blob_sha = license_data.get("evidence_blob_sha")
    if isinstance(blob_sha, str) and not SHA256_RE.fullmatch(blob_sha):
        errors.append(f"{prefix}.license.evidence_blob_sha must be a full blob SHA")
    return errors


def _decision_errors(source: dict[str, Any], prefix: str) -> list[str]:
    errors: list[str] = []
    decision = source.get("decision")
    materialization = source.get("materialization")
    profile = source.get("profile")
    if decision in MATERIALIZABLE_DECISIONS and (
        not isinstance(profile, str) or not profile.strip()
    ):
        errors.append(f"{prefix}.profile is required for materializable sources")
    if decision == "REFERENCE" and materialization != "none":
        errors.append(f"{prefix}.reference sources must not materialize")
    if decision == "TOOL" and source.get("kind") != "tool-provider":
        errors.append(f"{prefix}.TOOL decision requires tool-provider kind")
    return errors


def _source_errors(source: object, index: int) -> list[str]:
    prefix = f"sources[{index}]"
    if not isinstance(source, dict):
        return [f"{prefix} must be an object"]
    return [
        *_required_string_errors(source, prefix),
        *_identity_errors(source, prefix),
        *_enum_errors(source, prefix),
        *_safety_errors(source, prefix),
        *_license_errors(source, prefix),
        *_decision_errors(source, prefix),
    ]


def _policy_errors(data: dict[str, Any]) -> list[str]:
    policy = data.get("policy")
    if not isinstance(policy, dict):
        return ["policy must be an object"]
    required_false = (
        "vendor_source_into_divan",
        "floating_refs_allowed",
        "unknown_project_mcp_auto_approval",
    )
    return [
        f"policy.{field} must remain false"
        for field in required_false
        if policy.get(field) is not False
    ]


def _duplicate_errors(sources: list[object]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, set[str]] = {"id": set(), "repository": set()}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for field, label in (("id", "source id"), ("repository", "repository")):
            value = source.get(field)
            if not isinstance(value, str):
                continue
            if value in seen[field]:
                errors.append(f"duplicate {label}: {value}")
            seen[field].add(value)
    return errors


def registry_errors(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["registry root must be an object"]
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("autonomy") != "never-auto-install":
        errors.append("autonomy must remain never-auto-install")
    errors.extend(_policy_errors(data))
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return [*errors, "sources must be a non-empty list"]
    for index, source in enumerate(sources):
        errors.extend(_source_errors(source, index))
    errors.extend(_duplicate_errors(sources))
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
