"""Privacy-bounded adoption receipts for Divan Project OS."""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import re
from typing import Any

import goals
import project_state
import receipts

HOSTS = frozenset({"claude-code", "codex", "cursor", "other"})
SUBMITTERS = frozenset({"maintainer", "independent"})
VERIFIED_STATES = frozenset({"VERIFIED", "RELEASED", "OBSERVED"})
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
EMAIL = re.compile(r"(?i)\b[^@\s]+@[^@\s]+\.[^@\s]+\b")
REMOTE = re.compile(r"(?i)\b(?:https?|ssh|git)://|\bgit@[\w.-]+:")
JSON_MARKER_START = "<!-- DIVAN_ADOPTION_JSON\n"
JSON_MARKER_END = "DIVAN_ADOPTION_JSON -->"
RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "product",
        "divan",
        "host",
        "environment",
        "project",
        "goal",
        "declaration",
        "receipt_digest",
    }
)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _digest(value: dict[str, Any]) -> str:
    material = {
        key: item for key, item in value.items() if key != "receipt_digest"
    }
    canonical = json.dumps(
        material, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _coarse_environment() -> dict[str, str]:
    system = platform.system().casefold()
    operating_system = {
        "windows": "windows",
        "linux": "linux",
        "darwin": "macos",
    }.get(system, "other")
    machine = platform.machine().casefold()
    architecture = (
        "arm64"
        if machine in {"aarch64", "arm64"}
        else "x86_64"
        if machine in {"amd64", "x86_64"}
        else "other"
    )
    return {"os": operating_system, "architecture": architecture}


def _read_config(root: pathlib.Path) -> dict[str, Any]:
    path = root / ".divan" / "config.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Divan project config is unavailable or unsafe")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 2:
        raise ValueError("Divan project config schema 2 is required")
    return value


def _privacy_errors(value: Any, label: str = "receipt") -> list[str]:
    errors = receipts._redaction_errors(value, label)
    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_privacy_errors(item, f"{label}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_privacy_errors(item, f"{label}[{index}]"))
    elif isinstance(value, str):
        if EMAIL.search(value):
            errors.append(f"{label} contains an email address")
        if REMOTE.search(value):
            errors.append(f"{label} contains a remote URL")
    return sorted(set(errors))


def _check_summary(verification: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for identifier, result in sorted(verification.get("results", {}).items()):
        evidence = result.get("evidence", [])
        hashes = [
            "sha256:" + hashlib.sha256(item.encode("utf-8")).hexdigest()
            for item in evidence
            if isinstance(item, str)
        ]
        summary[identifier] = {
            "status": result.get("status"),
            "evidence_hashes": hashes,
        }
    return summary


def _markdown(value: dict[str, Any]) -> bytes:
    goal = value["goal"]
    host = value["host"]
    body = (
        "# Divan Adoption Receipt\n\n"
        f"- Status: `{goal['state']}`\n"
        f"- Host: `{host['name']} {host['version']}`\n"
        f"- Submitter: `{value['declaration']['submitter']}`\n"
        f"- Receipt: `{value['receipt_digest']}`\n\n"
        f"{JSON_MARKER_START}"
        f"{_json_bytes(value).decode('utf-8')}"
        f"{JSON_MARKER_END}\n"
    )
    return body.encode("utf-8")


def export_adoption(
    project: pathlib.Path | str,
    goal_id: str,
    host: str,
    host_version: str,
    submitter: str = "maintainer",
) -> dict[str, Any]:
    """Write deterministic JSON and Markdown acceptance receipts."""
    root = pathlib.Path(project).resolve()
    if host not in HOSTS:
        raise ValueError("host is unsupported")
    if submitter not in SUBMITTERS:
        raise ValueError("submitter must be maintainer or independent")
    if not isinstance(host_version, str) or not SAFE_TOKEN.fullmatch(host_version):
        raise ValueError("host version is unsafe")
    state, state_errors = project_state.load_install_state(root)
    if state is None or state_errors:
        raise ValueError("Divan install state is invalid")
    source = state["installed"]
    if str(source["source_ref"]).startswith("development@"):
        raise ValueError("adoption export requires an immutable release source")
    _spec, _evidence, receipt_path = goals._goal_paths(root, goal_id)
    verification = receipts.verify_receipt(receipt_path)
    if not verification["ok"] or verification["state"] not in VERIFIED_STATES:
        raise ValueError("goal receipt must be verified before adoption export")
    config = _read_config(root)
    receipt_value = json.loads(receipt_path.read_text(encoding="utf-8"))
    value = {
        "schema_version": 1,
        "product": "divan-adoption",
        "divan": {
            "version": source["version"],
            "ref": source["source_ref"],
            "commit": source["source_commit"],
        },
        "host": {"name": host, "version": host_version},
        "environment": _coarse_environment(),
        "project": {
            "identity_sha256": state["project_identity"],
            "types": sorted(config.get("project_types", [])),
            "workspace_count": len(config.get("workspaces", [])),
        },
        "goal": {
            "id": goal_id,
            "state": verification["state"],
            "target": receipt_value["target"],
            "receipt_sha256": (
                "sha256:" + hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            ),
            "artifact_sha256": sorted(
                f"sha256:{digest}"
                for digest in verification["artifacts"].values()
            ),
            "checks": _check_summary(verification),
        },
        "declaration": {"submitter": submitter},
    }
    value["receipt_digest"] = _digest(value)
    errors = _privacy_errors(value)
    if errors:
        raise ValueError("; ".join(errors))
    base = root / ".divan" / "evidence" / goal_id
    json_path = base / "adoption-receipt.json"
    markdown_path = base / "adoption-receipt.md"
    goals._atomic_write(json_path, _json_bytes(value))
    goals._atomic_write(markdown_path, _markdown(value))
    return {
        "schema_version": 1,
        "status": (
            "valid-owner-canary"
            if submitter == "maintainer"
            else "valid-independent-declaration"
        ),
        "json": json_path.relative_to(root).as_posix(),
        "markdown": markdown_path.relative_to(root).as_posix(),
        "receipt_digest": value["receipt_digest"],
    }


def _read_receipt(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.casefold() == ".md":
        if JSON_MARKER_START not in text or JSON_MARKER_END not in text:
            raise ValueError("Markdown adoption receipt has no JSON envelope")
        text = text.split(JSON_MARKER_START, 1)[1].split(
            JSON_MARKER_END, 1
        )[0]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("adoption receipt root must be an object")
    return value


def verify_adoption(path: pathlib.Path | str) -> dict[str, Any]:
    """Verify receipt schema, digest, privacy, and declared independence."""
    errors: list[str] = []
    try:
        value = _read_receipt(pathlib.Path(path))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {"schema_version": 1, "status": "invalid", "errors": [str(error)]}
    if set(value) != RECEIPT_KEYS:
        errors.append("adoption receipt keys are invalid")
    if value.get("schema_version") != 1 or value.get("product") != "divan-adoption":
        errors.append("adoption receipt identity is invalid")
    if value.get("receipt_digest") != _digest(value):
        errors.append("adoption receipt digest does not match")
    divan = value.get("divan")
    if not isinstance(divan, dict) or not HEX_40.fullmatch(
        str(divan.get("commit", ""))
    ):
        errors.append("Divan source identity is invalid")
    host = value.get("host")
    if (
        not isinstance(host, dict)
        or host.get("name") not in HOSTS
        or not SAFE_TOKEN.fullmatch(str(host.get("version", "")))
    ):
        errors.append("host declaration is invalid")
    declaration = value.get("declaration")
    submitter = declaration.get("submitter") if isinstance(declaration, dict) else None
    if submitter not in SUBMITTERS:
        errors.append("submitter declaration is invalid")
    goal = value.get("goal")
    if (
        not isinstance(goal, dict)
        or goal.get("state") not in VERIFIED_STATES
        or not SHA256.fullmatch(str(goal.get("receipt_sha256", "")))
    ):
        errors.append("goal evidence is invalid")
    errors.extend(_privacy_errors(value))
    return {
        "schema_version": 1,
        "status": (
            "invalid"
            if errors
            else "valid-owner-canary"
            if submitter == "maintainer"
            else "valid-independent-declaration"
        ),
        "errors": sorted(set(errors)),
    }
