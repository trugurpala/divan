#!/usr/bin/env python3
"""Claude ve Codex yerel pazarlarinin ayni Divan'i sundugunu denetle."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent.parent


def _read_json(path: pathlib.Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing marketplace or manifest: {path.relative_to(path.parent.parent)}")
        return {}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path}")
        return {}
    return value


def _plugin_index(
    marketplace: dict[str, Any], host: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    plugins = marketplace.get("plugins", [])
    if not isinstance(plugins, list):
        errors.append(f"{host} marketplace plugins must be an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for plugin in plugins:
        if not isinstance(plugin, dict) or not isinstance(plugin.get("name"), str):
            errors.append(f"{host} marketplace contains an invalid plugin entry: {plugin!r}")
            continue
        name = plugin["name"]
        if name in result:
            errors.append(f"{host} marketplace repeats plugin {name}")
        result[name] = plugin
    return result


def _source(plugin: dict[str, Any], host: str) -> str | None:
    source = plugin.get("source")
    if host == "claude":
        return source if isinstance(source, str) else None
    if not isinstance(source, dict) or source.get("source") != "local":
        return None
    path = source.get("path")
    return path if isinstance(path, str) else None


def _normalized_source(source: str | None) -> str | None:
    if source is None:
        return None
    return pathlib.PurePosixPath(source.replace("\\", "/")).as_posix().removeprefix("./")


def check(root: pathlib.Path = ROOT) -> tuple[list[str], int, int]:
    """Return errors, shared package count, and repository skill count."""
    errors: list[str] = []
    claude_marketplace = _read_json(root / ".claude-plugin" / "marketplace.json", errors)
    codex_marketplace = _read_json(root / ".agents" / "plugins" / "marketplace.json", errors)
    claude = _plugin_index(claude_marketplace, "claude", errors)
    codex = _plugin_index(codex_marketplace, "codex", errors)

    if set(claude) != set(codex):
        errors.append(
            "host package sets differ: "
            f"claude={sorted(claude)} codex={sorted(codex)}"
        )

    for name in sorted(set(claude) | set(codex)):
        if name not in claude or name not in codex:
            continue
        claude_entry = claude[name]
        codex_entry = codex[name]
        claude_source = _normalized_source(_source(claude_entry, "claude"))
        codex_source = _normalized_source(_source(codex_entry, "codex"))
        if not claude_source or not codex_source or claude_source != codex_source:
            errors.append(
                f"{name}: source drift: claude={claude_source!r} codex={codex_source!r}"
            )
        if claude_entry.get("version") != codex_entry.get("version"):
            errors.append(
                f"{name}: version drift: claude={claude_entry.get('version')!r} "
                f"codex={codex_entry.get('version')!r}"
            )

        if not claude_source:
            continue
        package_dir = root / claude_source
        for host, manifest_dir in (
            ("claude", ".claude-plugin"),
            ("codex", ".codex-plugin"),
        ):
            manifest = _read_json(package_dir / manifest_dir / "plugin.json", errors)
            if manifest.get("name") != name:
                errors.append(f"{name}: {host} manifest name does not match")
            expected_version = claude_entry.get("version")
            if manifest.get("version") != expected_version:
                errors.append(
                    f"{name}: {host} manifest version {manifest.get('version')!r} "
                    f"does not match marketplace version {expected_version!r}"
                )
            if host == "codex" and manifest.get("skills") != "./skills/":
                errors.append(f"{name}: codex manifest skills must be './skills/'")

    skills = len(list(root.glob("plugins/*/skills/*/SKILL.md")))
    return errors, len(set(claude) & set(codex)), skills


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without changing files")
    args = parser.parse_args()
    if not args.check:
        parser.error("only --check is supported")
    errors, packages, skills = check()
    if errors:
        print("HOST MARKETPLACE CHECK FAILED")
        for error in errors:
            print(f"  X {error}")
        return 1
    print(f"HOST MARKETPLACES OK - {packages} packages, {skills} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
