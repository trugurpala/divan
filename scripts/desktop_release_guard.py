#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import tomllib
from typing import Any, Mapping

ROOT = pathlib.Path(__file__).resolve().parents[1]
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_CORE_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


class DesktopReleaseError(ValueError):
    pass


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DesktopReleaseError(f"{label} must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesktopReleaseError(f"{label} must be a non-empty string")
    return value.strip()


def _git_sha(value: object, label: str) -> str:
    text = _text(value, label).casefold()
    if not _GIT_SHA_RE.fullmatch(text):
        raise DesktopReleaseError(f"{label} must be a full 40-character Git SHA")
    return text


def _sha256(value: object, label: str) -> str:
    text = _text(value, label).casefold()
    if not _SHA256_RE.fullmatch(text):
        raise DesktopReleaseError(f"{label} must be a full 64-character SHA-256")
    return text


def _semver_core(value: object, label: str) -> tuple[int, int, int]:
    text = _text(value, label)
    match = _SEMVER_CORE_RE.fullmatch(text)
    if match is None:
        raise DesktopReleaseError(f"{label} must be a semantic version")
    return tuple(int(part) for part in match.groups())


def _deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _read_json(path: pathlib.Path, label: str) -> Mapping[str, Any]:
    return _mapping(json.loads(path.read_text(encoding="utf-8-sig")), label)


def _desktop_inputs(root: pathlib.Path) -> tuple[str, Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    desktop = root / "apps" / "desktop"
    tauri_root = desktop / "src-tauri"
    version = _text((root / "VERSION").read_text(encoding="utf-8"), "VERSION")
    package = _read_json(desktop / "package.json", "package.json")
    tauri = _read_json(tauri_root / "tauri.conf.json", "tauri.conf.json")
    windows = _read_json(tauri_root / "tauri.windows.conf.json", "tauri.windows.conf.json")
    cargo = _mapping(
        tomllib.loads((tauri_root / "Cargo.toml").read_text(encoding="utf-8")),
        "Cargo.toml",
    )
    return version, package, tauri, windows, cargo


def _verify_versions(
    version: str,
    package: Mapping[str, Any],
    tauri: Mapping[str, Any],
    cargo: Mapping[str, Any],
) -> None:
    cargo_package = _mapping(cargo.get("package"), "Cargo package")
    versions = {
        "VERSION": version,
        "package.json": _text(package.get("version"), "package version"),
        "tauri.conf.json": _text(tauri.get("version"), "tauri version"),
        "Cargo.toml": _text(cargo_package.get("version"), "Cargo version"),
    }
    if len(set(versions.values())) != 1:
        raise DesktopReleaseError(f"desktop version drift: {versions}")


def _verify_identity(tauri: Mapping[str, Any]) -> None:
    expected = {
        "productName": "Divan",
        "mainBinaryName": "Divan",
        "identifier": "com.ugurpala.divan",
    }
    for key, value in expected.items():
        if tauri.get(key) != value:
            raise DesktopReleaseError(f"unexpected Tauri {key}: {tauri.get(key)!r}")


def _merged_config(
    tauri: Mapping[str, Any],
    windows: Mapping[str, Any],
    release_config: pathlib.Path | None,
) -> Mapping[str, Any]:
    merged = _deep_merge(tauri, windows)
    if release_config is None:
        return merged
    return _deep_merge(merged, _read_json(release_config, "desktop release config"))


def _bundle_contract(config: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    bundle = _mapping(config.get("bundle"), "Tauri bundle")
    windows_bundle = _mapping(bundle.get("windows"), "Tauri Windows bundle")
    nsis = _mapping(windows_bundle.get("nsis"), "Tauri NSIS bundle")
    if nsis.get("installMode") != "currentUser":
        raise DesktopReleaseError("NSIS installMode must remain currentUser")
    external_bin = bundle.get("externalBin")
    if not isinstance(external_bin, list) or "binaries/divan-core" not in external_bin:
        raise DesktopReleaseError("Divan Core sidecar is missing from Windows bundle")
    return bundle, windows_bundle


def _updater_ready(config: Mapping[str, Any], bundle: Mapping[str, Any]) -> bool:
    plugins = config.get("plugins")
    if not isinstance(plugins, Mapping):
        return False
    updater = plugins.get("updater")
    if not isinstance(updater, Mapping):
        return False
    pubkey = updater.get("pubkey")
    endpoints = updater.get("endpoints")
    return bool(
        bundle.get("createUpdaterArtifacts") is True
        and isinstance(pubkey, str)
        and pubkey.strip()
        and isinstance(endpoints, list)
        and endpoints
        and all(isinstance(item, str) and item.startswith("https://") for item in endpoints)
    )


def _windows_signing_ready(windows_bundle: Mapping[str, Any]) -> bool:
    sign_command = windows_bundle.get("signCommand")
    return bool(
        isinstance(sign_command, str)
        and sign_command.strip()
        and "%1" in sign_command
        and "\n" not in sign_command
        and "\r" not in sign_command
    )


def inspect_acceptance_evidence(
    path: pathlib.Path,
    expected_version: str,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"))
    evidence = _mapping(value, "Windows acceptance evidence")
    required = {
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
    }
    for key, expected in required.items():
        if evidence.get(key) != expected:
            raise DesktopReleaseError(
                f"Windows acceptance evidence requires {key}={expected!r}"
            )
    worker = evidence.get("worker_agent")
    reviewer = evidence.get("reviewer")
    if worker not in {"codex", "claude"}:
        raise DesktopReleaseError("Windows release acceptance worker must be Codex or Claude")
    if reviewer not in {"codex", "claude"}:
        raise DesktopReleaseError("Windows acceptance evidence has an unsupported reviewer")
    if reviewer == worker:
        raise DesktopReleaseError("Windows release acceptance requires a cross-agent reviewer")
    source_commit = _git_sha(evidence.get("source_commit"), "acceptance source_commit")
    source_tree = _git_sha(evidence.get("source_tree"), "acceptance source_tree")
    core_commit = _git_sha(evidence.get("core_source_commit"), "Core source_commit")
    core_tree = _git_sha(evidence.get("core_source_tree"), "Core source_tree")
    review_diff_sha256 = _sha256(
        evidence.get("review_diff_sha256"),
        "acceptance review_diff_sha256",
    )
    merged_commit_sha = _git_sha(
        evidence.get("merged_commit_sha"),
        "acceptance merged_commit_sha",
    )
    if core_commit != source_commit or core_tree != source_tree:
        raise DesktopReleaseError("installed Divan Core does not match the accepted source identity")
    expected_commit = (
        _git_sha(expected_source_commit, "expected source commit")
        if expected_source_commit is not None
        else None
    )
    expected_tree = (
        _git_sha(expected_source_tree, "expected source tree")
        if expected_source_tree is not None
        else None
    )
    if expected_commit is not None and source_commit != expected_commit:
        raise DesktopReleaseError("Windows acceptance evidence does not match the release source commit")
    if expected_tree is not None and source_tree != expected_tree:
        raise DesktopReleaseError("Windows acceptance evidence does not match the release source tree")
    kinds = evidence.get("evidence_kinds")
    required_kinds = {"execution", "review", "approval"}
    if not isinstance(kinds, list) or not required_kinds.issubset({str(item) for item in kinds}):
        raise DesktopReleaseError(
            "Windows acceptance evidence must include execution, review and approval"
        )
    source_bound = expected_commit is not None and expected_tree is not None
    return {
        "accepted": True,
        "source_bound": source_bound,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "core_source_commit": core_commit,
        "core_source_tree": core_tree,
        "review_diff_sha256": review_diff_sha256,
        "merged_commit_sha": merged_commit_sha,
        "worker_agent": worker,
        "reviewer": reviewer,
    }


def inspect_updater_e2e_evidence(
    path: pathlib.Path,
    expected_version: str,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"))
    evidence = _mapping(value, "signed updater E2E evidence")
    required = {
        "schema_version": 1,
        "status": "pass",
        "valid_signed_upgrade": True,
        "tampered_signature_rejected": True,
        "forward_signed_recovery": True,
        "downgrade_not_offered": True,
        "signatures_mandatory": True,
        "test_only_insecure_transport": True,
        "production_transport_policy": "https-only",
    }
    for key, expected in required.items():
        if evidence.get(key) != expected:
            raise DesktopReleaseError(
                f"signed updater E2E evidence requires {key}={expected!r}"
            )

    source_commit = _git_sha(evidence.get("source_commit"), "updater E2E source_commit")
    source_tree = _git_sha(evidence.get("source_tree"), "updater E2E source_tree")
    baseline_version = _text(evidence.get("baseline_version"), "updater E2E baseline_version")
    upgraded_version = _text(evidence.get("upgraded_version"), "updater E2E upgraded_version")
    recovered_version = _text(evidence.get("recovered_version"), "updater E2E recovered_version")
    if baseline_version != expected_version:
        raise DesktopReleaseError(
            "signed updater E2E baseline version does not match the release version"
        )
    baseline_core = _semver_core(baseline_version, "updater E2E baseline_version")
    upgraded_core = _semver_core(upgraded_version, "updater E2E upgraded_version")
    recovered_core = _semver_core(recovered_version, "updater E2E recovered_version")
    if not baseline_core < upgraded_core < recovered_core:
        raise DesktopReleaseError(
            "signed updater E2E versions must prove monotonic N -> N+1 -> N+2 recovery"
        )

    expected_commit = (
        _git_sha(expected_source_commit, "expected source commit")
        if expected_source_commit is not None
        else None
    )
    expected_tree = (
        _git_sha(expected_source_tree, "expected source tree")
        if expected_source_tree is not None
        else None
    )
    if expected_commit is not None and source_commit != expected_commit:
        raise DesktopReleaseError("signed updater E2E evidence does not match the release source commit")
    if expected_tree is not None and source_tree != expected_tree:
        raise DesktopReleaseError("signed updater E2E evidence does not match the release source tree")

    digest_fields = (
        "baseline_installer_sha256",
        "upgrade_installer_sha256",
        "recovery_installer_sha256",
        "baseline_signature_sha256",
        "upgrade_signature_sha256",
        "recovery_signature_sha256",
    )
    digests = {
        field: _sha256(evidence.get(field), f"updater E2E {field}")
        for field in digest_fields
    }
    source_bound = expected_commit is not None and expected_tree is not None
    return {
        "verified": True,
        "source_bound": source_bound,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "baseline_version": baseline_version,
        "upgraded_version": upgraded_version,
        "recovered_version": recovered_version,
        "digests": digests,
    }


def inspect_desktop(
    root: pathlib.Path = ROOT,
    *,
    release_config: pathlib.Path | None = None,
    acceptance_evidence: pathlib.Path | None = None,
    updater_e2e_evidence: pathlib.Path | None = None,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    version, package, tauri, windows, cargo = _desktop_inputs(root)
    _verify_versions(version, package, tauri, cargo)
    _verify_identity(tauri)
    config = _merged_config(tauri, windows, release_config)
    bundle, windows_bundle = _bundle_contract(config)
    acceptance = (
        inspect_acceptance_evidence(
            acceptance_evidence,
            version,
            expected_source_commit=expected_source_commit,
            expected_source_tree=expected_source_tree,
        )
        if acceptance_evidence is not None
        else None
    )
    updater_e2e = (
        inspect_updater_e2e_evidence(
            updater_e2e_evidence,
            version,
            expected_source_commit=expected_source_commit,
            expected_source_tree=expected_source_tree,
        )
        if updater_e2e_evidence is not None
        else None
    )
    return {
        "status": "PASS",
        "version": version,
        "product": "Divan",
        "main_binary": "Divan.exe",
        "installer": "nsis-current-user",
        "core_sidecar": True,
        "updater_configured": _updater_ready(config, bundle),
        "windows_signing_configured": _windows_signing_ready(windows_bundle),
        "acceptance_evidence": acceptance,
        "updater_e2e_evidence": updater_e2e,
    }


def require_stable_release(
    report: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    environment = os.environ if env is None else env
    blockers: list[str] = []
    if report.get("updater_configured") is not True:
        blockers.append("signed Tauri updater is not configured")
    if not environment.get("TAURI_SIGNING_PRIVATE_KEY"):
        blockers.append("TAURI_SIGNING_PRIVATE_KEY is missing")
    if report.get("windows_signing_configured") is not True:
        blockers.append("Windows Authenticode signCommand is not configured")
    updater_e2e = report.get("updater_e2e_evidence")
    if not isinstance(updater_e2e, Mapping) or updater_e2e.get("verified") is not True:
        blockers.append("signed updater E2E evidence is missing")
    elif updater_e2e.get("source_bound") is not True:
        blockers.append("signed updater E2E evidence is not bound to the exact release source identity")
    acceptance = report.get("acceptance_evidence")
    if not isinstance(acceptance, Mapping) or acceptance.get("accepted") is not True:
        blockers.append("real-user Windows acceptance evidence is missing")
    elif acceptance.get("source_bound") is not True:
        blockers.append("Windows acceptance evidence is not bound to the exact release source identity")
    if blockers:
        raise DesktopReleaseError("stable desktop release blocked: " + "; ".join(blockers))
    return {**dict(report), "stable_release": "READY"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--release-config", type=pathlib.Path)
    parser.add_argument("--acceptance-evidence", type=pathlib.Path)
    parser.add_argument("--updater-e2e-evidence", type=pathlib.Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--source-tree")
    parser.add_argument("--stable-release", action="store_true")
    args = parser.parse_args()
    try:
        report = inspect_desktop(
            args.root,
            release_config=args.release_config,
            acceptance_evidence=args.acceptance_evidence,
            updater_e2e_evidence=args.updater_e2e_evidence,
            expected_source_commit=args.source_commit,
            expected_source_tree=args.source_tree,
        )
        if args.stable_release:
            report = require_stable_release(report)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, DesktopReleaseError) as error:
        parser.error(str(error))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
