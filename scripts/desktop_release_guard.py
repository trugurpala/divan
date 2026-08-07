#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def inspect_desktop(root: pathlib.Path = ROOT) -> dict[str, Any]:
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

    bundle = _mapping(tauri_root.get("bundle"), "Tauri bundle")
    windows_bundle = _mapping(bundle.get("windows"), "Tauri Windows bundle")
    nsis = _mapping(windows_bundle.get("nsis"), "Tauri NSIS bundle")
    if nsis.get("installMode") != "currentUser":
        raise DesktopReleaseError("NSIS installMode must remain currentUser")

    windows_root = _mapping(windows, "tauri.windows.conf.json")
    external_bin = _mapping(windows_root.get("bundle"), "Windows bundle").get(
        "externalBin"
    )
    if not isinstance(external_bin, list) or "binaries/divan-core" not in external_bin:
        raise DesktopReleaseError("Divan Core sidecar is missing from Windows bundle")

    updater = tauri_root.get("plugins")
    updater_config = None
    if isinstance(updater, Mapping):
        candidate = updater.get("updater")
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

    return {
        "status": "PASS",
        "version": version,
        "product": "Divan",
        "main_binary": "Divan.exe",
        "installer": "nsis-current-user",
        "core_sidecar": True,
        "updater_configured": updater_ready,
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
    if environment.get("DIVAN_WINDOWS_CODE_SIGNING_READY") != "1":
        blockers.append("Windows Authenticode signing is not marked ready")
    if blockers:
        raise DesktopReleaseError("stable desktop release blocked: " + "; ".join(blockers))
    return {**dict(report), "stable_release": "READY"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--stable-release", action="store_true")
    args = parser.parse_args()
    try:
        report = inspect_desktop(args.root)
        if args.stable_release:
            report = require_stable_release(report)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, DesktopReleaseError) as error:
        parser.error(str(error))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
