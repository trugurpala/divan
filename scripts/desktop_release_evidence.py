from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
from typing import Any, Mapping

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_CORE_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


class DesktopReleaseError(ValueError):
    pass


def mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DesktopReleaseError(f"{label} must be an object")
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesktopReleaseError(f"{label} must be a non-empty string")
    return value.strip()


def git_sha(value: object, label: str) -> str:
    result = text(value, label).casefold()
    if not _GIT_SHA_RE.fullmatch(result):
        raise DesktopReleaseError(f"{label} must be a full 40-character Git SHA")
    return result


def sha256(value: object, label: str) -> str:
    result = text(value, label).casefold()
    if not _SHA256_RE.fullmatch(result):
        raise DesktopReleaseError(f"{label} must be a full 64-character SHA-256")
    return result


def semver_core(value: object, label: str) -> tuple[int, int, int]:
    result = text(value, label)
    match = _SEMVER_CORE_RE.fullmatch(result)
    if match is None:
        raise DesktopReleaseError(f"{label} must be a semantic version")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def _utc_timestamp(value: object, label: str) -> tuple[str, dt.datetime]:
    result = text(value, label)
    try:
        parsed = dt.datetime.fromisoformat(result.replace("Z", "+00:00"))
    except ValueError as error:
        raise DesktopReleaseError(f"{label} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DesktopReleaseError(f"{label} must include a UTC offset")
    return result, parsed.astimezone(dt.timezone.utc)


def _load_evidence(path: pathlib.Path, label: str) -> tuple[bytes, Mapping[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"))
    return raw, mapping(value, label)


def _require_fields(
    evidence: Mapping[str, Any],
    required: Mapping[str, object],
    label: str,
) -> None:
    for key, expected in required.items():
        if evidence.get(key) != expected:
            raise DesktopReleaseError(f"{label} requires {key}={expected!r}")


def _expected_source(
    source_commit: str,
    source_tree: str,
    expected_source_commit: str | None,
    expected_source_tree: str | None,
    *,
    label: str,
) -> bool:
    expected_commit = (
        git_sha(expected_source_commit, "expected source commit")
        if expected_source_commit is not None
        else None
    )
    expected_tree = (
        git_sha(expected_source_tree, "expected source tree")
        if expected_source_tree is not None
        else None
    )
    if expected_commit is not None and source_commit != expected_commit:
        raise DesktopReleaseError(f"{label} does not match the release source commit")
    if expected_tree is not None and source_tree != expected_tree:
        raise DesktopReleaseError(f"{label} does not match the release source tree")
    return expected_commit is not None and expected_tree is not None


def inspect_production_readiness_evidence(
    path: pathlib.Path,
    expected_version: str,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    raw, evidence = _load_evidence(path, "production readiness evidence")
    _require_fields(
        evidence,
        {
            "schema_version": 1,
            "status": "pass",
            "product": "Divan Desktop",
            "version": expected_version,
            "production_environment": "production-release",
            "release_overlay_valid": True,
            "updater_public_key_configured": True,
            "updater_endpoint_https": True,
            "artifact_base_exact_release_tag": True,
            "authenticode_sign_command_usable": True,
            "authenticode_signature_valid": True,
            "tauri_private_key_sign_probe": True,
            "private_signing_material_persisted": False,
            "secret_values_in_evidence": False,
        },
        "production readiness evidence",
    )
    password_configured = evidence.get("tauri_private_key_password_configured")
    if not isinstance(password_configured, bool):
        raise DesktopReleaseError(
            "production readiness evidence tauri_private_key_password_configured must be boolean"
        )
    source_commit = git_sha(
        evidence.get("source_commit"),
        "production readiness source_commit",
    )
    source_tree = git_sha(
        evidence.get("source_tree"),
        "production readiness source_tree",
    )
    source_bound = _expected_source(
        source_commit,
        source_tree,
        expected_source_commit,
        expected_source_tree,
        label="production readiness evidence",
    )
    public_key_hash = sha256(
        evidence.get("updater_public_key_sha256"),
        "production readiness updater_public_key_sha256",
    )
    signer_hash = sha256(
        evidence.get("authenticode_signer_thumbprint_sha256"),
        "production readiness authenticode_signer_thumbprint_sha256",
    )
    not_after_text, not_after = _utc_timestamp(
        evidence.get("authenticode_certificate_not_after_utc"),
        "production readiness authenticode_certificate_not_after_utc",
    )
    if not_after <= dt.datetime.now(dt.timezone.utc):
        raise DesktopReleaseError("production readiness Authenticode certificate is expired")
    return {
        "verified": True,
        "source_bound": source_bound,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "version": expected_version,
        "updater_public_key_sha256": public_key_hash,
        "authenticode_signer_thumbprint_sha256": signer_hash,
        "authenticode_certificate_not_after_utc": not_after_text,
        "tauri_private_key_password_configured": password_configured,
    }


def _acceptance_agents(evidence: Mapping[str, Any]) -> tuple[object, object]:
    worker = evidence.get("worker_agent")
    reviewer = evidence.get("reviewer")
    if worker not in {"codex", "claude"}:
        raise DesktopReleaseError("Windows release acceptance worker must be Codex or Claude")
    if reviewer not in {"codex", "claude"}:
        raise DesktopReleaseError("Windows acceptance evidence has an unsupported reviewer")
    if reviewer == worker:
        raise DesktopReleaseError("Windows release acceptance requires a cross-agent reviewer")
    return worker, reviewer


def _acceptance_identity(
    evidence: Mapping[str, Any],
) -> tuple[str, str, str, str, str, str]:
    source_commit = git_sha(evidence.get("source_commit"), "acceptance source_commit")
    source_tree = git_sha(evidence.get("source_tree"), "acceptance source_tree")
    core_commit = git_sha(evidence.get("core_source_commit"), "Core source_commit")
    core_tree = git_sha(evidence.get("core_source_tree"), "Core source_tree")
    review_diff = sha256(evidence.get("review_diff_sha256"), "acceptance review_diff_sha256")
    merged_commit = git_sha(
        evidence.get("merged_commit_sha"),
        "acceptance merged_commit_sha",
    )
    if core_commit != source_commit or core_tree != source_tree:
        raise DesktopReleaseError("installed Divan Core does not match the accepted source identity")
    return source_commit, source_tree, core_commit, core_tree, review_diff, merged_commit


def _require_acceptance_kinds(evidence: Mapping[str, Any]) -> None:
    kinds = evidence.get("evidence_kinds")
    required = {"execution", "review", "approval"}
    if not isinstance(kinds, list) or not required.issubset({str(item) for item in kinds}):
        raise DesktopReleaseError(
            "Windows acceptance evidence must include execution, review and approval"
        )


def inspect_acceptance_evidence(
    path: pathlib.Path,
    expected_version: str,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    raw, evidence = _load_evidence(path, "Windows acceptance evidence")
    _require_fields(
        evidence,
        {
            "schema_version": 3,
            "product": "Divan",
            "version": expected_version,
            "platform": "windows",
            "result": "PASS",
            "authenticated_worker": True,
            "authenticated_reviewer": True,
            "independent_reviewer": True,
            "review_bound_to_diff": True,
            "ff_only_merge": True,
            "task_state": "merged",
        },
        "Windows acceptance evidence",
    )
    worker, reviewer = _acceptance_agents(evidence)
    identity = _acceptance_identity(evidence)
    source_commit, source_tree, core_commit, core_tree, review_diff, merged_commit = identity
    source_bound = _expected_source(
        source_commit,
        source_tree,
        expected_source_commit,
        expected_source_tree,
        label="Windows acceptance evidence",
    )
    _require_acceptance_kinds(evidence)
    return {
        "accepted": True,
        "source_bound": source_bound,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "core_source_commit": core_commit,
        "core_source_tree": core_tree,
        "review_diff_sha256": review_diff,
        "merged_commit_sha": merged_commit,
        "worker_agent": worker,
        "reviewer": reviewer,
    }


def _updater_versions(
    evidence: Mapping[str, Any],
    expected_version: str,
) -> tuple[str, str, str]:
    baseline = text(evidence.get("baseline_version"), "updater E2E baseline_version")
    upgraded = text(evidence.get("upgraded_version"), "updater E2E upgraded_version")
    recovered = text(evidence.get("recovered_version"), "updater E2E recovered_version")
    if baseline != expected_version:
        raise DesktopReleaseError(
            "signed updater E2E baseline version does not match the release version"
        )
    if not (
        semver_core(baseline, "updater E2E baseline_version")
        < semver_core(upgraded, "updater E2E upgraded_version")
        < semver_core(recovered, "updater E2E recovered_version")
    ):
        raise DesktopReleaseError(
            "signed updater E2E versions must prove monotonic N -> N+1 -> N+2 recovery"
        )
    return baseline, upgraded, recovered


def _updater_digests(evidence: Mapping[str, Any]) -> dict[str, str]:
    fields = (
        "baseline_installer_sha256",
        "upgrade_installer_sha256",
        "recovery_installer_sha256",
        "baseline_signature_sha256",
        "upgrade_signature_sha256",
        "recovery_signature_sha256",
    )
    return {field: sha256(evidence.get(field), f"updater E2E {field}") for field in fields}


def inspect_updater_e2e_evidence(
    path: pathlib.Path,
    expected_version: str,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    raw, evidence = _load_evidence(path, "signed updater E2E evidence")
    _require_fields(
        evidence,
        {
            "schema_version": 1,
            "status": "pass",
            "valid_signed_upgrade": True,
            "tampered_signature_rejected": True,
            "forward_signed_recovery": True,
            "downgrade_not_offered": True,
            "signatures_mandatory": True,
            "test_only_insecure_transport": True,
            "production_transport_policy": "https-only",
        },
        "signed updater E2E evidence",
    )
    source_commit = git_sha(evidence.get("source_commit"), "updater E2E source_commit")
    source_tree = git_sha(evidence.get("source_tree"), "updater E2E source_tree")
    baseline, upgraded, recovered = _updater_versions(evidence, expected_version)
    source_bound = _expected_source(
        source_commit,
        source_tree,
        expected_source_commit,
        expected_source_tree,
        label="signed updater E2E evidence",
    )
    return {
        "verified": True,
        "source_bound": source_bound,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "baseline_version": baseline,
        "upgraded_version": upgraded,
        "recovered_version": recovered,
        "digests": _updater_digests(evidence),
    }
