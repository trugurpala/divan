#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
from typing import Mapping
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ReleaseConfigError(ValueError):
    pass


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ReleaseConfigError(f"{name} is required")
    return value


def _https_endpoint(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ReleaseConfigError("DIVAN_UPDATER_ENDPOINT must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ReleaseConfigError("DIVAN_UPDATER_ENDPOINT must not contain credentials")
    return value


def _sign_command(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ReleaseConfigError("DIVAN_WINDOWS_SIGN_COMMAND must be a single line")
    if "%1" not in value:
        raise ReleaseConfigError("DIVAN_WINDOWS_SIGN_COMMAND must contain Tauri's %1 file placeholder")
    if len(value) > 2048:
        raise ReleaseConfigError("DIVAN_WINDOWS_SIGN_COMMAND is unexpectedly long")
    return value


def build_release_overlay(
    root: pathlib.Path = ROOT,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    environment = os.environ if env is None else env
    windows_config = json.loads(
        (root / "apps" / "desktop" / "src-tauri" / "tauri.windows.conf.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(windows_config, dict):
        raise ReleaseConfigError("tauri.windows.conf.json must contain an object")

    pubkey = _required(environment, "DIVAN_UPDATER_PUBKEY")
    endpoint = _https_endpoint(_required(environment, "DIVAN_UPDATER_ENDPOINT"))
    sign_command = _sign_command(_required(environment, "DIVAN_WINDOWS_SIGN_COMMAND"))

    bundle = windows_config.setdefault("bundle", {})
    if not isinstance(bundle, dict):
        raise ReleaseConfigError("Windows bundle configuration must be an object")
    bundle["createUpdaterArtifacts"] = True
    windows = bundle.setdefault("windows", {})
    if not isinstance(windows, dict):
        raise ReleaseConfigError("Windows signing configuration must be an object")
    windows["signCommand"] = sign_command

    plugins = windows_config.setdefault("plugins", {})
    if not isinstance(plugins, dict):
        raise ReleaseConfigError("plugins configuration must be an object")
    plugins["updater"] = {"pubkey": pubkey, "endpoints": [endpoint]}
    return windows_config


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an ephemeral Tauri overlay for a signed Divan Desktop release."
    )
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        overlay = build_release_overlay(args.root.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ReleaseConfigError) as error:
        parser.error(str(error))
    print(str(args.output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
