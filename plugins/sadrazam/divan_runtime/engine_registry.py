#!/usr/bin/env python3
"""Validate Divan multi-engine registry metadata without running engines."""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any, TypeGuard

SCHEMA_VERSION = 1
COMMAND = "engines validate"
ROOT_FIELDS = {"schema_version", "engines"}
ENGINE_FIELDS = {
    "id",
    "decision",
    "status",
    "license",
    "source",
    "fork_repository",
    "host_compatibility",
    "supported_project_types",
    "forbidden_project_types",
    "quality_profiles",
    "installation",
    "escape_plan",
    "portability",
    "business_logic_ownership",
    "frontend_replaceability",
    "when_unavailable",
}
REQUIRED_ENGINE_FIELDS = ENGINE_FIELDS - {"fork_repository"}
DECISIONS = {"ADOPT", "ADAPT", "REFERENCE", "FORK"}
STATUSES = {"candidate", "active", "accepted", "adapted", "deprecated", "blocked"}
UNKNOWN_LICENSES = {"UNKNOWN", "NOASSERTION"}
PIN_POLICIES = {"immutable", "lockfile", "manual"}
LOCKFILE_DECISIONS = {"ADOPT", "ADAPT"}
HOSTS = {"claude", "codex", "standalone"}
PROJECT_TYPES = {
    "api",
    "automation",
    "cms",
    "desktop",
    "documentation",
    "internal-app",
    "library",
    "monorepo",
    "public-web",
    "quality",
    "service",
}
QUALITY_PROFILES = {
    "api-provider-v1",
    "documentation-provider-v1",
    "internal-app-v1",
    "portal-provider-v1",
    "typescript-monorepo-v1",
}
INSTALLATION_MODES = {"dependency", "fork", "none", "provider", "sidecar", "vendored"}
BUSINESS_OWNERS = {"community", "project", "vendor"}
UNAVAILABLE = {"degrade", "fallback", "manual", "readonly"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SPDX_TOKEN_RE = re.compile(r"^[A-Za-z0-9.+-]+$")
URL_RE = re.compile(r"^https://\S+$")


Issue = dict[str, str]


def validate_registry_path(path: pathlib.Path | str) -> tuple[dict[str, Any], int]:
    """Validate a registry JSON file and return a stable result plus exit code."""
    registry = pathlib.Path(path)
    result = _base_result(registry)
    try:
        text = registry.read_text(encoding="utf-8")
    except FileNotFoundError:
        _add(result, "REGISTRY_FILE_NOT_FOUND", "$", f"registry not found: {_display(registry)}")
        return _finish(result, 2)
    except UnicodeDecodeError:
        _add(result, "REGISTRY_INVALID_UTF8", "$", "registry file is not valid UTF-8")
        return _finish(result, 2)
    except OSError as error:
        _add(result, "REGISTRY_FILE_NOT_FOUND", "$", f"registry cannot be read: {error.__class__.__name__}")
        return _finish(result, 2)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        _add(result, "REGISTRY_INVALID_JSON", "$", "registry file is not valid JSON")
        return _finish(result, 1)
    return validate_registry_payload(payload, _display(registry))


def validate_registry_payload(payload: Any, registry: str) -> tuple[dict[str, Any], int]:
    """Validate a loaded registry value and return a stable result plus exit code."""
    result = _base_result(registry)
    if not isinstance(payload, dict):
        _add(result, "REGISTRY_ROOT_INVALID", "$", "registry root must be an object")
        return _finish(result, 1)
    _unknown_fields(result, "$", payload, ROOT_FIELDS, "REGISTRY_UNKNOWN_FIELD")
    if payload.get("schema_version") != SCHEMA_VERSION:
        _add(result, "REGISTRY_SCHEMA_VERSION_INVALID", "$.schema_version", "schema_version must be 1")
    engines = payload.get("engines")
    if engines is None:
        _add(result, "ENGINES_REQUIRED", "$.engines", "engines array is required")
        return _finish(result, 1)
    if not isinstance(engines, list):
        _add(result, "ENGINES_REQUIRED", "$.engines", "engines must be an array")
        return _finish(result, 1)
    seen: set[str] = set()
    for index, engine in enumerate(engines):
        _validate_engine(result, f"$.engines[{index}]", engine, seen)
    return _finish(result, 0 if not result["errors"] else 1)


def _validate_engine(result: dict[str, Any], path: str, engine: Any, seen: set[str]) -> None:
    if not isinstance(engine, dict):
        _add(result, "ENGINE_INVALID", path, "engine entry must be an object")
        return
    result["engine_count"] += 1
    _unknown_fields(result, path, engine, ENGINE_FIELDS, "ENGINE_UNKNOWN_FIELD")
    _required_fields(result, path, engine)
    engine_id = engine.get("id")
    if not _string(engine_id) or not ID_RE.fullmatch(engine_id):
        _add(result, "ENGINE_ID_INVALID", f"{path}.id", "engine id must be lowercase kebab-case")
    elif engine_id in seen:
        _add(result, "ENGINE_DUPLICATE_ID", f"{path}.id", f"duplicate engine id: {engine_id}")
    if _string(engine_id):
        seen.add(engine_id)
    _enum(result, path, engine, "decision", DECISIONS, "ENGINE_DECISION_INVALID")
    _enum(result, path, engine, "status", STATUSES, "ENGINE_STATUS_INVALID")
    _validate_license(result, path, engine.get("license"))
    _validate_source(result, path, engine)
    _validate_lists(result, path, engine)
    _validate_installation(result, path, engine.get("installation"))
    _validate_escape_plan(result, path, engine.get("escape_plan"))
    _validate_portability(result, path, engine)


def _required_fields(result: dict[str, Any], path: str, engine: dict[str, Any]) -> None:
    code_by_field = {
        "escape_plan": "ENGINE_ESCAPE_PLAN_REQUIRED",
        "license": "ENGINE_LICENSE_REQUIRED",
        "source": "ENGINE_SOURCE_REQUIRED",
    }
    for field in sorted(REQUIRED_ENGINE_FIELDS - set(engine)):
        code = code_by_field.get(field, "ENGINE_INVALID")
        _add(result, code, f"{path}.{field}", f"{field} is required")


def _validate_license(result: dict[str, Any], path: str, value: Any) -> None:
    if not isinstance(value, dict):
        return
    expression = value.get("spdx_expression")
    evidence = value.get("evidence")
    if not _string(expression) or not _valid_spdx(expression):
        _add(result, "ENGINE_LICENSE_INVALID", f"{path}.license.spdx_expression", "license must use SPDX or UNKNOWN")
    if not _string(evidence) or not URL_RE.fullmatch(evidence):
        _add(result, "ENGINE_LICENSE_EVIDENCE_REQUIRED", f"{path}.license.evidence", "license evidence URL is required")


def _valid_spdx(value: str) -> bool:
    if value in UNKNOWN_LICENSES:
        return True
    parts = value.replace("(", " ").replace(")", " ").split()
    if not parts:
        return False
    operators = {"AND", "OR", "WITH"}
    return all(part in operators or SPDX_TOKEN_RE.fullmatch(part) for part in parts)


def _validate_source(result: dict[str, Any], path: str, engine: dict[str, Any]) -> None:
    source = engine.get("source")
    if not isinstance(source, dict):
        return
    upstream = source.get("url")
    pin = source.get("pin")
    policy = source.get("pin_policy")
    decision = engine.get("decision")
    status = engine.get("status")
    if not _string(upstream) or not URL_RE.fullmatch(upstream):
        _add(result, "ENGINE_SOURCE_REQUIRED", f"{path}.source.url", "canonical upstream URL is required")
    if policy not in PIN_POLICIES:
        _add(result, "ENGINE_PIN_REQUIRED", f"{path}.source.pin_policy", "pin_policy must be immutable, lockfile, or manual")
    if policy == "lockfile" and decision not in LOCKFILE_DECISIONS:
        _add(result, "ENGINE_PIN_REQUIRED", f"{path}.source.pin_policy", "lockfile pin policy is limited to ADOPT or ADAPT")
    if status in {"active", "accepted"} and (policy != "immutable" or not _commit(pin)):
        _add(result, "ENGINE_PIN_REQUIRED", f"{path}.source.pin", "active or accepted engines require an immutable commit pin")
    if policy == "immutable" and pin is not None and not _commit(pin):
        _add(result, "ENGINE_PIN_REQUIRED", f"{path}.source.pin", "immutable pin must be a 40-character lowercase commit")
    _validate_fork(result, path, engine, upstream)


def _validate_fork(result: dict[str, Any], path: str, engine: dict[str, Any], upstream: Any) -> None:
    decision = engine.get("decision")
    fork = engine.get("fork_repository")
    if decision == "FORK":
        if not _string(fork) or not URL_RE.fullmatch(fork):
            _add(result, "ENGINE_FORK_URL_REQUIRED", f"{path}.fork_repository", "FORK requires fork_repository URL")
        elif _string(upstream) and fork == upstream:
            _add(result, "ENGINE_FORK_URL_INVALID", f"{path}.fork_repository", "fork URL cannot equal upstream URL")
    elif fork is not None:
        _add(result, "ENGINE_FORK_URL_INVALID", f"{path}.fork_repository", "fork_repository is allowed only for FORK")


def _validate_lists(result: dict[str, Any], path: str, engine: dict[str, Any]) -> None:
    _list_values(result, path, engine, "host_compatibility", HOSTS, "ENGINE_HOST_COMPATIBILITY_INVALID", False)
    _list_values(result, path, engine, "supported_project_types", PROJECT_TYPES, "ENGINE_PROJECT_TYPE_INVALID", True)
    _list_values(result, path, engine, "forbidden_project_types", PROJECT_TYPES, "ENGINE_PROJECT_TYPE_INVALID", True)
    _list_values(result, path, engine, "quality_profiles", QUALITY_PROFILES, "ENGINE_QUALITY_PROFILE_INVALID", False)
    supported = set(_strings(engine.get("supported_project_types")))
    forbidden = set(_strings(engine.get("forbidden_project_types")))
    if supported & forbidden:
        _add(result, "ENGINE_PORTABILITY_CONTRADICTION", f"{path}.forbidden_project_types", "project type cannot be both supported and forbidden")


def _list_values(
    result: dict[str, Any],
    path: str,
    engine: dict[str, Any],
    field: str,
    allowed: set[str],
    code: str,
    allow_empty: bool,
) -> None:
    value = engine.get(field)
    if not isinstance(value, list) or (not allow_empty and not value):
        _add(result, code, f"{path}.{field}", f"{field} must be a list")
        return
    for item in value:
        if not _string(item) or item not in allowed:
            _add(result, code, f"{path}.{field}", f"invalid {field} value: {item}")
            return


def _validate_installation(result: dict[str, Any], path: str, value: Any) -> None:
    if not isinstance(value, dict):
        return
    modes = value.get("modes")
    if not isinstance(modes, list) or not modes:
        _add(result, "ENGINE_INSTALLATION_MODE_INVALID", f"{path}.installation.modes", "installation modes are required")
    elif any(not _string(mode) or mode not in INSTALLATION_MODES for mode in modes):
        _add(result, "ENGINE_INSTALLATION_MODE_INVALID", f"{path}.installation.modes", "installation mode is invalid")
    for field in ("removal", "rollback"):
        if not _string(value.get(field)):
            _add(result, "ENGINE_INSTALLATION_MODE_INVALID", f"{path}.installation.{field}", f"{field} statement is required")


def _validate_escape_plan(result: dict[str, Any], path: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        _add(result, "ENGINE_ESCAPE_PLAN_INVALID", f"{path}.escape_plan", "escape_plan must be an object")
        return
    if not _string(value.get("summary")):
        _add(result, "ENGINE_ESCAPE_PLAN_INVALID", f"{path}.escape_plan.summary", "escape summary is required")
    steps = value.get("steps")
    if not isinstance(steps, list) or not steps or any(not _string(step) for step in steps):
        _add(result, "ENGINE_ESCAPE_PLAN_INVALID", f"{path}.escape_plan.steps", "escape steps must be non-empty strings")


def _validate_portability(result: dict[str, Any], path: str, engine: dict[str, Any]) -> None:
    portability = engine.get("portability")
    ownership = engine.get("business_logic_ownership")
    frontend = engine.get("frontend_replaceability")
    if not isinstance(portability, dict) or not isinstance(portability.get("data_portable"), bool):
        _add(result, "ENGINE_PORTABILITY_INVALID", f"{path}.portability.data_portable", "data_portable boolean is required")
        return
    if portability.get("data_portable") is False:
        _add(result, "ENGINE_PORTABILITY_CONTRADICTION", f"{path}.portability.data_portable", "engine data must remain portable")
    if not isinstance(ownership, dict) or ownership.get("owner") not in BUSINESS_OWNERS or not _string(ownership.get("notes")):
        _add(result, "ENGINE_BUSINESS_LOGIC_INVALID", f"{path}.business_logic_ownership", "business logic ownership declaration is required")
    if not isinstance(frontend, dict) or not isinstance(frontend.get("replaceable"), bool) or not _string(frontend.get("notes")):
        _add(result, "ENGINE_FRONTEND_REPLACEABILITY_INVALID", f"{path}.frontend_replaceability", "frontend replaceability declaration is required")
    if engine.get("when_unavailable") not in UNAVAILABLE:
        _add(result, "ENGINE_UNAVAILABLE_BEHAVIOR_INVALID", f"{path}.when_unavailable", "unavailable behavior statement is required")


def _base_result(registry: pathlib.Path | str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": COMMAND,
        "status": "valid",
        "registry": _display(registry),
        "engine_count": 0,
        "error_count": 0,
        "warning_count": 0,
        "errors": [],
        "warnings": [],
    }


def _finish(result: dict[str, Any], exit_code: int) -> tuple[dict[str, Any], int]:
    result["errors"].sort(key=lambda row: (row["path"], row["code"], row["message"]))
    result["warnings"].sort(key=lambda row: (row["path"], row["code"], row["message"]))
    result["error_count"] = len(result["errors"])
    result["warning_count"] = len(result["warnings"])
    if result["errors"]:
        result["status"] = "invalid"
    return result, exit_code


def _add(result: dict[str, Any], code: str, path: str, message: str) -> None:
    result["errors"].append({"code": code, "path": path, "message": message})


def _unknown_fields(
    result: dict[str, Any], path: str, value: dict[str, Any], allowed: set[str], code: str
) -> None:
    for field in sorted(set(value) - allowed):
        _add(result, code, f"{path}.{field}", f"unknown field: {field}")


def _enum(result: dict[str, Any], path: str, engine: dict[str, Any], field: str, allowed: set[str], code: str) -> None:
    if engine.get(field) not in allowed:
        _add(result, code, f"{path}.{field}", f"{field} is invalid")


def _string(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str)) if isinstance(value, list) else ()


def _commit(value: Any) -> bool:
    return isinstance(value, str) and COMMIT_RE.fullmatch(value) is not None


def _display(path: pathlib.Path | str) -> str:
    value = pathlib.Path(path)
    if not value.is_absolute():
        return value.as_posix()
    try:
        return value.resolve(strict=False).relative_to(pathlib.Path.cwd().resolve()).as_posix()
    except ValueError:
        return value.name
