#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import tomllib
from typing import Any, Mapping

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def _deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def inspect_acceptance_evidence(path: pathlib.Path, expected_version: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    evidence = _mapping(value, "Windows acceptance evidence")
    required = {
        "schema_version": 1,
        "product": "Divan",
        "version": expected_version,
        "platform": "windows",
        "result": "PASS",
        "authenticated_worker": True,
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
    if worker not in {"codex", "claude", "opencode", "cursor-agent"}:
        raise DesktopReleaseError("Windows acceptance evidence has an unsupported worker")
    if reviewer not in {"codex", "claude"}:
        raise DesktopReleaseError("Windows acceptance evidence has an unsupported reviewer")
    kinds = evidence.get("evidence_kinds")
    if not isinstance(kinds, list) or not {"execution", "review", "approval"}.issubset(
        {str(item) for item in kinds}
    ):
        raise DesktopReleaseError(
            "Windows acceptance evidence must include execution, review and approval"
        )
    return {
        "accepted": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "worker_agent": worker,
        "reviewer": reviewer,
    }


def inspect_desktop(
    root: pathlib.Path = ROOT,
    *,
    release_config: pathlib.Path | None = None,
    acceptance_evidence: pathlib.Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    version = _text((root / "VERSION").read_text(encoding="utf-8"), "VERSION")
    package = json.loads(
        (root / "apps" / "desktop" / "package.json").read_text(encoding="utf-8")
    )
    tauri = json.loads(
        (root / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(
            encoding="utf-8"
        )
    )
    windows = json.loads(
        (
            root
            / "apps"
            / "desktop"
            / "src-tauri"
            / "tauri.windows.conf.json"
        ).read_text(encoding="utf-8")
    )
    cargo = tomllib.loads(
        (root / "apps" / "desktop" / "src-tauri" / "Cargo.toml").read_text(
            encoding="utf-8"
        )
    )

    package_version = _text(
        _mapping(package, "package.json").get("version"), "package version"
    )
    tauri_version = _text(
        _mapping(tauri, "tauri.conf.json").get("version"), "tauri version"
    )
    cargo_version = _text(
        _mapping(_mapping(cargo, "Cargo.toml").get("package"), "Cargo package").get(
            "version"
        ),
        "Cargo version",
    )
    versions = {
        "VERSION": version,
        "package.json": package_version,
        "tauri.conf.json": tauri_version,
        "Cargo.toml": cargo_version,
    }
    if len(set(versions.values())) != 1:
        raise DesktopReleaseError(f"desktop version drift: {versions}")

    tauri_root = _mapping(tauri, "tauri.conf.json")
    if tauri_root.get("productName") != "Divan":
        raise DesktopReleaseError("Tauri productName must be Divan")
    if tauri_root.get("mainBinaryName") != "Divan":
        raise DesktopReleaseError("Tauri mainBinaryName must be Divan")
    if tauri_root.get("identifier") != "com.ugurpala.divan":
        raise DesktopReleaseError("unexpected Tauri application identifier")

    merged_config = _deep_merge(tauri_root, _mapping(windows, "tauri.windows.conf.json"))
    if release_config is not None:
        release_value = json.loads(release_config.read_text(encoding="utf-8"))
        merged_config = _deep_merge(
            merged_config,
            _mapping(release_value, "desktop release config"),
        )

    bundle = _mapping(merged_config.get("bundle"), "Tauri bundle")
    windows_bundle = _mapping(bundle.get("windows"), "Tauri Windows bundle")
    nsis = _mapping(windows_bundle.get("nsis"), "Tauri NSIS bundle")
    if nsis.get("installMode") != "currentUser":
        raise DesktopReleaseError("NSIS installMode must remain currentUser")

    external_bin = bundle.get("externalBin")
    if not isinstance(external_bin, list) or "binaries/divan-core" not in external_bin:
        raise DesktopReleaseError("Divan Core sidecar is missing from Windows bundle")

    plugins = merged_config.get("plugins")
    updater_config = None
    if isinstance(plugins, Mapping):
        candidate = plugins.get("updater")
        if isinstance(candidate, Mapping):
            updater_config = candidate
    endpoints = updater_config.get("endpoints") if updater_config else None
    updater_ready = bool(
        bundle.get("createUpdaterArtifacts") is True
        and updater_config
        and isinstance(updater_config.get("pubkey"), str)
        and updater_config.get("pubkey", "").strip()
        and isinstance(endpoints, list)
        and endpoints
        and all(isinstance(item, str) and item.startswith("https://") for item in endpoints)
    )
    sign_command = windows_bundle.get("signCommand")
    windows_signing = bool(
        isinstance(sign_command, str)
        and sign_command.strip()
        and "%1" in sign_command
        and "\n" not in sign_command
        and "\r" not in sign_command
    )

    report: dict[str, Any] = {
        "status": "PASS",
        "version": version,
        "product": "Divan",
        "main_binary": "Divan.exe",
        "installer": "nsis-current-user",
        "core_sidecar": True,
        "updater_configured": updater_ready,
        "windows_signing_configured": windows_signing,
        "acceptance_evidence": None,
    }
    if acceptance_evidence is not None:
        report["acceptance_evidence"] = inspect_acceptance_evidence(
            acceptance_evidence,
            version,
        )
    return report


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
    acceptance = report.get("acceptance_evidence")
    if not isinstance(acceptance, Mapping) or acceptance.get("accepted") is not True:
        blockers.append("real-user Windows acceptance evidence is missing")
    if blockers:
        raise DesktopReleaseError("stable desktop release blocked: " + "; ".join(blockers))
    return {**dict(report), "stable_release": "READY"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--release-config", type=pathlib.Path)
    parser.add_argument("--acceptance-evidence", type=pathlib.Path)
    parser.add_argument("--stable-release", action="store_true")
    args = parser.parse_args()
    try:
        report = inspect_desktop(
            args.root,
            release_config=args.release_config,
            acceptance_evidence=args.acceptance_evidence,
        )
        if args.stable_release:
            report = require_stable_release(report)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, DesktopReleaseError) as error:
        parser.error(str(error))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
