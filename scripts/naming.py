#!/usr/bin/env python3
"""Enforce English-canonical technical filenames and bounded legacy aliases."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any, cast

POLICY = pathlib.Path("registry/naming-policy.json")
TECHNICAL_SUFFIXES = {".py", ".ps1", ".sh", ".yml", ".yaml"}


def _read_policy(root: pathlib.Path) -> dict[str, Any]:
    path = root / POLICY
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid naming policy: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("invalid naming policy schema")
    return value


def legacy_wrapper_errors(path: pathlib.Path, replacement: str) -> list[str]:
    """Return compatibility-wrapper violations without executing the file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"legacy alias is unreadable: {path}: {exc}"]
    errors: list[str] = []
    if "deprecated" not in text.lower():
        errors.append(f"legacy alias lacks deprecation notice: {path}")
    if pathlib.PurePosixPath(replacement).name not in text:
        errors.append(f"legacy alias lacks replacement: {path}")
    if len(text.splitlines()) > 20:
        errors.append(f"legacy alias is not a narrow wrapper: {path}")
    return errors


def _technical_paths(root: pathlib.Path) -> list[pathlib.Path]:
    paths = [
        path
        for directory in (root / "scripts", root / ".github" / "workflows")
        if directory.is_dir()
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in TECHNICAL_SUFFIXES
    ]
    return sorted(paths)


def _tokens(path: pathlib.Path) -> set[str]:
    return {
        token
        for token in re.split(r"[-_.]+", path.name.lower())
        if token
    }


def _policy_shape_errors(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("canonical_language") != "en" or policy.get("locales") != ["en", "tr"]:
        errors.append("naming policy must be English-canonical with en/tr locales")
    for key, kind in (
        ("canonical_entrypoints", str),
        ("legacy_aliases", dict),
        ("disallowed_non_english_tokens", str),
    ):
        value = policy.get(key)
        if not isinstance(value, list) or not all(isinstance(item, kind) for item in value):
            errors.append(f"{key} must be a {kind.__name__} list")
    return errors


def _alias_errors(repository: pathlib.Path, aliases: list[dict[str, Any]]) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    paths: set[str] = set()
    for row in aliases:
        path, replacement = row.get("path"), row.get("replacement")
        if not isinstance(path, str) or not isinstance(replacement, str):
            errors.append("legacy alias requires path and replacement")
            continue
        paths.add(path)
        source, target = repository / path, repository / replacement
        if not source.is_file():
            errors.append(f"legacy alias is missing: {path}")
        if not target.is_file():
            errors.append(f"legacy replacement is missing: {replacement}")
        if path.endswith(".py") and source.is_file():
            errors.extend(legacy_wrapper_errors(source, replacement))
    return errors, paths


def _technical_path_errors(
    repository: pathlib.Path, blocked: set[str], aliases: set[str]
) -> list[str]:
    errors: list[str] = []
    for path in _technical_paths(repository):
        relative = path.relative_to(repository).as_posix()
        if not path.name.isascii():
            errors.append(f"technical filename is not ASCII: {relative}")
        if _tokens(path) & blocked and relative not in aliases:
            errors.append(f"unregistered technical name: {relative}")
    return errors


def validate(root: pathlib.Path | None = None) -> list[str]:
    """Validate naming policy, canonical files, and compatibility aliases."""
    repository = (root or pathlib.Path(__file__).resolve().parent.parent).resolve()
    try:
        policy = _read_policy(repository)
    except ValueError as exc:
        return [str(exc)]
    errors = _policy_shape_errors(policy)
    canonical = policy.get("canonical_entrypoints")
    aliases = policy.get("legacy_aliases")
    disallowed = policy.get("disallowed_non_english_tokens")
    if errors:
        return errors
    canonical = cast(list[str], canonical)
    aliases = cast(list[dict[str, Any]], aliases)
    disallowed = cast(list[str], disallowed)
    for relative in canonical:
        if not (repository / relative).is_file():
            errors.append(f"canonical entrypoint is missing: {relative}")
    alias_errors, alias_paths = _alias_errors(repository, aliases)
    errors.extend(alias_errors)
    errors.extend(_technical_path_errors(repository, set(disallowed), alias_paths))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args(argv)
    errors = validate()
    result = {"status": "valid" if not errors else "invalid", "errors": errors}
    if options.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("NAMING POLICY VALID")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
