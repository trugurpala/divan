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
DIVAN_KEYS = frozenset({"version", "ref", "commit"})
HOST_KEYS = frozenset({"name", "version"})
ENVIRONMENT_KEYS = frozenset({"os", "architecture"})
PROJECT_KEYS = frozenset({"identity_sha256", "types", "workspace_count"})
GOAL_KEYS = frozenset(
    {
        "id",
        "state",
        "target",
        "receipt_sha256",
        "artifact_sha256",
        "checks",
    }
)
CHECK_KEYS = frozenset({"status", "evidence_hashes"})
DECLARATION_KEYS = frozenset({"submitter"})
PROJECT_TYPES = frozenset(
    {"application", "documentation", "library", "monorepo", "public-web", "service"}
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


def _schema_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    divan = value.get("divan")
    if not isinstance(divan, dict) or set(divan) != DIVAN_KEYS:
        errors.append("Divan source keys are invalid")
    elif (
        project_state.SEMVER.fullmatch(str(divan.get("version", ""))) is None
        or project_state.IMMUTABLE_REF.fullmatch(str(divan.get("ref", ""))) is None
        or HEX_40.fullmatch(str(divan.get("commit", ""))) is None
    ):
        errors.append("Divan source identity is invalid")
    host = value.get("host")
    if (
        not isinstance(host, dict)
        or set(host) != HOST_KEYS
        or host.get("name") not in HOSTS
        or SAFE_TOKEN.fullmatch(str(host.get("version", ""))) is None
    ):
        errors.append("host declaration is invalid")
    environment = value.get("environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != ENVIRONMENT_KEYS
        or environment.get("os") not in {"windows", "linux", "macos", "other"}
        or environment.get("architecture") not in {"x86_64", "arm64", "other"}
    ):
        errors.append("environment summary is invalid")
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != PROJECT_KEYS:
        errors.append("project summary keys are invalid")
    else:
        project_types = project.get("types")
        if (
            not isinstance(project_types, list)
            or project_types != sorted(set(project_types))
            or not all(item in PROJECT_TYPES for item in project_types)
            or type(project.get("workspace_count")) is not int
            or project["workspace_count"] < 0
            or SHA256.fullmatch(str(project.get("identity_sha256", ""))) is None
        ):
            errors.append("project summary is invalid")
    goal = value.get("goal")
    if not isinstance(goal, dict) or set(goal) != GOAL_KEYS:
        errors.append("goal evidence keys are invalid")
    else:
        hashes = goal.get("artifact_sha256")
        checks = goal.get("checks")
        if (
            goals.GOAL_ID_PATTERN.fullmatch(str(goal.get("id", ""))) is None
            or goal.get("state") not in VERIFIED_STATES
            or goal.get("target") not in receipts.TARGETS
            or SHA256.fullmatch(str(goal.get("receipt_sha256", ""))) is None
            or not isinstance(hashes, list)
            or hashes != sorted(hashes)
            or not hashes
            or not all(SHA256.fullmatch(str(item)) for item in hashes)
            or not isinstance(checks, dict)
        ):
            errors.append("goal evidence is invalid")
        elif any(
            not isinstance(result, dict)
            or set(result) != CHECK_KEYS
            or result.get("status") not in receipts.RESULT_STATES
            or not isinstance(result.get("evidence_hashes"), list)
            or not all(
                SHA256.fullmatch(str(item))
                for item in result.get("evidence_hashes", [])
            )
            for result in checks.values()
        ):
            errors.append("goal check summary is invalid")
    declaration = value.get("declaration")
    if (
        not isinstance(declaration, dict)
        or set(declaration) != DECLARATION_KEYS
        or declaration.get("submitter") not in SUBMITTERS
    ):
        errors.append("submitter declaration is invalid")
    return errors


def verify_adoption(path: pathlib.Path | str) -> dict[str, Any]:
    """Verify receipt schema, digest, privacy, and declared independence."""
    errors: list[str] = []
    receipt_path = pathlib.Path(path)
    try:
        raw_text = receipt_path.read_text(encoding="utf-8")
        value = _read_receipt(receipt_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {"schema_version": 1, "status": "invalid", "errors": [str(error)]}
    errors.extend(_privacy_errors(raw_text, "document"))
    if set(value) != RECEIPT_KEYS:
        errors.append("adoption receipt keys are invalid")
    if value.get("schema_version") != 1 or value.get("product") != "divan-adoption":
        errors.append("adoption receipt identity is invalid")
    if value.get("receipt_digest") != _digest(value):
        errors.append("adoption receipt digest does not match")
    errors.extend(_schema_errors(value))
    declaration = value.get("declaration")
    submitter = declaration.get("submitter") if isinstance(declaration, dict) else None
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
