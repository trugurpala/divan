"""Compatibility support for schema-1 adoption declarations."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any

from . import adoption_common as common
from . import goals, project_state, receipts

HOSTS = frozenset({"claude-code", "codex", "cursor", "other"})
SUBMITTERS = frozenset({"maintainer", "independent"})
VERIFIED_STATES = frozenset({"VERIFIED", "RELEASED", "OBSERVED"})
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
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


def _read_config(root: pathlib.Path) -> dict[str, Any]:
    path = root / ".divan" / "config.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("Divan project config is unavailable or unsafe")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 2:
        raise ValueError("Divan project config schema 2 is required")
    return value


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


def markdown(value: dict[str, Any]) -> bytes:
    goal = value["goal"]
    host = value["host"]
    body = (
        "# Divan Adoption Receipt\n\n"
        f"- Status: `{goal['state']}`\n"
        f"- Host: `{host['name']} {host['version']}`\n"
        f"- Submitter: `{value['declaration']['submitter']}`\n"
        f"- Receipt: `{value['receipt_digest']}`\n\n"
        f"{common.JSON_MARKER_START}"
        f"{common.json_bytes(value).decode('utf-8')}"
        f"{common.JSON_MARKER_END}\n"
    )
    return body.encode("utf-8")


def export_adoption(
    project: pathlib.Path | str,
    goal_id: str,
    host: str,
    host_version: str,
    submitter: str = "maintainer",
) -> dict[str, Any]:
    root = pathlib.Path(project).resolve()
    if host not in HOSTS:
        raise ValueError("host is unsupported")
    if submitter not in SUBMITTERS:
        raise ValueError("submitter must be maintainer or independent")
    if not isinstance(host_version, str) or not common.SAFE_TOKEN.fullmatch(host_version):
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
    value = _receipt_value(
        goal_id, host, host_version, state, source, verification, config,
        receipt_value, receipt_path, submitter
    )
    value["receipt_digest"] = common.digest_schema_1(value)
    errors = common.privacy_errors(value)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "schema_version": 1,
        "status": (
            "valid-schema-1-owner-canary"
            if submitter == "maintainer"
            else "valid-schema-1-independent-declaration"
        ),
        "json": common.json_bytes(value).decode("utf-8"),
        "markdown": markdown(value).decode("utf-8"),
        "receipt_digest": value["receipt_digest"],
    }


def _receipt_value(
    goal_id: str,
    host: str,
    host_version: str,
    state: dict[str, Any],
    source: dict[str, Any],
    verification: dict[str, Any],
    config: dict[str, Any],
    receipt_value: dict[str, Any],
    receipt_path: pathlib.Path,
    submitter: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "product": "divan-adoption",
        "divan": {
            "version": source["version"],
            "ref": source["source_ref"],
            "commit": source["source_commit"],
        },
        "host": {"name": host, "version": host_version},
        "environment": common.coarse_environment(),
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
                f"sha256:{digest}" for digest in verification["artifacts"].values()
            ),
            "checks": _check_summary(verification),
        },
        "declaration": {"submitter": submitter},
    }


def _schema_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_source_host_environment(value, errors)
    _validate_project(value, errors)
    _validate_goal(value, errors)
    declaration = value.get("declaration")
    if (
        not isinstance(declaration, dict)
        or set(declaration) != DECLARATION_KEYS
        or declaration.get("submitter") not in SUBMITTERS
    ):
        errors.append("submitter declaration is invalid")
    return errors


def _validate_source_host_environment(
    value: dict[str, Any], errors: list[str]
) -> None:
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
        or common.SAFE_TOKEN.fullmatch(str(host.get("version", ""))) is None
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


def _validate_project(value: dict[str, Any], errors: list[str]) -> None:
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != PROJECT_KEYS:
        errors.append("project summary keys are invalid")
        return
    project_types = project.get("types")
    if (
        not isinstance(project_types, list)
        or project_types != sorted(set(project_types))
        or not all(item in PROJECT_TYPES for item in project_types)
        or type(project.get("workspace_count")) is not int
        or project["workspace_count"] < 0
        or common.SHA256.fullmatch(str(project.get("identity_sha256", ""))) is None
    ):
        errors.append("project summary is invalid")


def _validate_goal(value: dict[str, Any], errors: list[str]) -> None:
    goal = value.get("goal")
    if not isinstance(goal, dict) or set(goal) != GOAL_KEYS:
        errors.append("goal evidence keys are invalid")
        return
    hashes = goal.get("artifact_sha256")
    checks = goal.get("checks")
    if (
        goals.GOAL_ID_PATTERN.fullmatch(str(goal.get("id", ""))) is None
        or goal.get("state") not in VERIFIED_STATES
        or goal.get("target") not in receipts.TARGETS
        or common.SHA256.fullmatch(str(goal.get("receipt_sha256", ""))) is None
        or not isinstance(hashes, list)
        or hashes != sorted(hashes)
        or not hashes
        or not all(common.SHA256.fullmatch(str(item)) for item in hashes)
        or not isinstance(checks, dict)
    ):
        errors.append("goal evidence is invalid")
        return
    if any(
        not isinstance(result, dict)
        or set(result) != CHECK_KEYS
        or result.get("status") not in receipts.RESULT_STATES
        or not isinstance(result.get("evidence_hashes"), list)
        or not all(
            common.SHA256.fullmatch(str(item))
            for item in result.get("evidence_hashes", [])
        )
        for result in checks.values()
    ):
        errors.append("goal check summary is invalid")


def verify_schema_1(value: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if set(value) != RECEIPT_KEYS:
        errors.append("adoption receipt keys are invalid")
    if value.get("schema_version") != 1 or value.get("product") != "divan-adoption":
        errors.append("adoption receipt identity is invalid")
    if value.get("receipt_digest") != common.digest_schema_1(value):
        errors.append("adoption receipt digest does not match")
    errors.extend(_schema_errors(value))
    declaration = value.get("declaration")
    submitter = declaration.get("submitter") if isinstance(declaration, dict) else None
    errors.extend(common.privacy_errors(value))
    return {
        "schema_version": 1,
        "status": (
            "invalid"
            if errors
            else "valid-schema-1-owner-canary"
            if submitter == "maintainer"
            else "valid-schema-1-independent-declaration"
        ),
        "eligible_for_v1": False,
        "errors": sorted(set(errors)),
    }
