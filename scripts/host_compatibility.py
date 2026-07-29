#!/usr/bin/env python3
"""Validate Divan's evidence-backed host compatibility registry."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOST_IDS = (
    "claude-code",
    "codex",
    "cursor",
    "antigravity-cli",
    "gemini-cli",
    "github-copilot",
    "kiro-ide",
    "kiro-cli",
    "opencode",
    "windsurf",
    "other-agents",
)
TIERS = ("experimental", "skill-compatible", "native", "verified")
CAPABILITIES = ("skills", "instructions", "commands", "agents", "hooks", "mcp", "lifecycle")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load(root: pathlib.Path = ROOT) -> Any:
    return json.loads((root / "registry" / "host-compatibility.json").read_text(encoding="utf-8"))


def _tier_errors(label: str, row: dict[str, Any]) -> list[str]:
    tier, target = row.get("tier"), row.get("target_tier")
    if tier not in TIERS or target not in TIERS:
        return [f"{label} has an unknown tier"]
    if TIERS.index(target) < TIERS.index(tier):
        return [f"{label}.target_tier cannot be lower than tier"]
    return []


def _capability_errors(label: str, capabilities: Any) -> list[str]:
    if not isinstance(capabilities, list) or not capabilities:
        return [f"{label}.capabilities must be a non-empty list"]
    if len(capabilities) != len(set(capabilities)) or any(
        capability not in CAPABILITIES for capability in capabilities
    ):
        return [f"{label}.capabilities contains duplicates or unknown values"]
    return []


def _evidence_errors(
    root: pathlib.Path, label: str, tier: Any, evidence: Any
) -> list[str]:
    if not isinstance(evidence, list):
        return [f"{label}.evidence must be a list"]
    errors: list[str] = []
    if tier == "verified" and not evidence:
        errors.append(f"{label}.evidence is required for verified hosts")
    if tier == "verified":
        for path in evidence:
            if not isinstance(path, str) or not (root / path).is_file():
                errors.append(f"{label}.evidence path is missing: {path}")
    return errors


def _host_errors(root: pathlib.Path, row: Any, index: int) -> list[str]:
    label = f"hosts[{index}]"
    if not isinstance(row, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    host_id = row.get("id")
    if not isinstance(host_id, str) or not ID_PATTERN.fullmatch(host_id):
        errors.append(f"{label}.id must be kebab-case ASCII")
    errors.extend(_tier_errors(label, row))
    errors.extend(_capability_errors(label, row.get("capabilities")))
    docs = row.get("official_docs")
    if not isinstance(docs, str) or not docs.startswith("https://"):
        errors.append(f"{label}.official_docs must be an HTTPS URL")
    errors.extend(_evidence_errors(root, label, row.get("tier"), row.get("evidence")))
    if not isinstance(row.get("distribution"), str) or not row["distribution"]:
        errors.append(f"{label}.distribution is required")
    return errors


def validate(root: pathlib.Path = ROOT) -> list[str]:
    try:
        data = load(root)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load host compatibility registry: {exc}"]
    if not isinstance(data, dict):
        return ["registry root must be an object"]
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("tiers") != list(TIERS):
        errors.append("tiers must match the canonical ordered set")
    if data.get("capabilities") != list(CAPABILITIES):
        errors.append("capabilities must match the canonical ordered set")
    hosts = data.get("hosts")
    if not isinstance(hosts, list):
        return [*errors, "hosts must be a list"]
    ids = [row.get("id") for row in hosts if isinstance(row, dict)]
    if ids != list(HOST_IDS):
        errors.append("hosts must match the canonical ordered host set")
    if len(ids) != len(set(ids)):
        errors.append("host ids must be unique")
    for index, row in enumerate(hosts):
        errors.extend(_host_errors(root, row, index))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.parse_args(argv)
    errors = validate()
    if "--json" in (argv or sys.argv[1:]):
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    elif errors:
        print("\n".join(f"HOST COMPATIBILITY: {error}" for error in errors))
    else:
        print(f"HOST COMPATIBILITY VALID - {len(HOST_IDS)} declared hosts")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
