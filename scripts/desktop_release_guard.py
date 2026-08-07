#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import tomllib
from typing import Any, Mapping

from desktop_release_evidence import (
    DesktopReleaseError,
    inspect_acceptance_evidence,
    inspect_updater_e2e_evidence,
)
from desktop_release_evidence import mapping as _mapping
from desktop_release_evidence import text as _text

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def _desktop_inputs(
    root: pathlib.Path,
) -> tuple[
    str,
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
    Mapping[str, Any],
]:
    desktop = root / "apps" / "desktop"
    tauri_root = desktop / "src-tauri"
    version = _text((root / "VERSION").read_text(encoding="utf-8"), "VERSION")
    package = _read_json(desktop / "package.json", "package.json")
    tauri = _read_json(tauri_root / "tauri.conf.json", "tauri.conf.json")
    windows = _read_json(
        tauri_root / "tauri.windows.conf.json",
        "tauri.windows.conf.json",
    )
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


def _bundle_contract(
    config: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
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
        and all(
            isinstance(item, str) and item.startswith("https://")
            for item in endpoints
        )
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
        blockers.append(
            "signed updater E2E evidence is not bound to the exact release source identity"
        )
    acceptance = report.get("acceptance_evidence")
    if not isinstance(acceptance, Mapping) or acceptance.get("accepted") is not True:
        blockers.append("real-user Windows acceptance evidence is missing")
    elif acceptance.get("source_bound") is not True:
        blockers.append(
            "Windows acceptance evidence is not bound to the exact release source identity"
        )
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
    except (
        OSError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        DesktopReleaseError,
    ) as error:
        parser.error(str(error))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
