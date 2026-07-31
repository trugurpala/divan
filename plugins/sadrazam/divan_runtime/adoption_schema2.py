"""Strict schema-2 clean-room adoption receipt contract."""
from __future__ import annotations

import copy
import re
from datetime import datetime
from typing import Any, cast

from . import adoption_common as common
from . import goals, project_state, receipts

RECEIPT_KEYS = frozenset(
    {
        "schema_version", "product", "divan", "host", "environment",
        "operator", "project", "goal", "checks", "proof",
    }
)
DIVAN_KEYS = frozenset(
    {"version", "ref", "commit", "distribution", "runner_sha256"}
)
HOST_KEYS = frozenset({"name", "version", "version_source"})
ENVIRONMENT_KEYS = frozenset({"os", "architecture"})
PROJECT_KEYS = frozenset(
    {
        "identity_sha256", "distinct_from_divan",
        "distinctness_policy_sha256", "types", "workspace_count",
    }
)
GOAL_KEYS = frozenset(
    {"id", "state", "target", "receipt_sha256", "artifact_sha256"}
)
CHECK_KEYS = frozenset(
    {
        "id", "class", "workspace_sha256", "runner", "name",
        "argv_sha256", "status", "exit_code", "duration_ms", "timeout_ms",
        "timeout_policy_sha256", "output_sha256",
    }
)
OPERATOR_KEYS = frozenset({"role"})
PROOF_KEYS = frozenset(
    {"id", "started_at", "completed_at", "source_stable", "receipt_digest"}
)
PROJECT_TYPES = frozenset(
    {"application", "documentation", "library", "monorepo", "public-web", "service"}
)
QUALIFYING_HOSTS = frozenset({"claude-code", "codex"})
OPERATOR_ROLES = frozenset({"maintainer", "external"})
CHECK_CLASSES = frozenset({"test", "regression", "typecheck", "check", "lint", "build"})
TEST_CLASSES = frozenset({"test", "regression"})
VERIFIED_STATES = frozenset({"VERIFIED", "RELEASED", "OBSERVED"})
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
PROOF_ID = re.compile(r"^proof-[0-9a-f]{12}$")
CHECK_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}:[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
)
RFC3339_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


def _timestamp(value: object, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or RFC3339_UTC.fullmatch(value) is None:
        errors.append(f"{label} must be an RFC3339 UTC timestamp")
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not a real timestamp")
        return None


def _exact_integer(value: object, label: str, errors: list[str]) -> int | None:
    if type(value) is not int:
        errors.append(f"{label} must be an integer")
        return None
    return value


def _source_errors(value: dict[str, Any]) -> list[str]:
    divan = value.get("divan")
    if not isinstance(divan, dict) or set(divan) != DIVAN_KEYS:
        return ["Divan source keys are invalid"]
    version = divan.get("version")
    if (
        not isinstance(version, str)
        or project_state.SEMVER.fullmatch(version) is None
        or divan.get("ref") != f"v{version}"
        or HEX_40.fullmatch(str(divan.get("commit", ""))) is None
        or divan.get("distribution") != "immutable-release"
        or common.SHA256.fullmatch(str(divan.get("runner_sha256", ""))) is None
    ):
        return ["Divan source identity is invalid"]
    return []


def _host_environment_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    host = value.get("host")
    if (
        not isinstance(host, dict)
        or set(host) != HOST_KEYS
        or host.get("name") not in QUALIFYING_HOSTS
        or common.SAFE_TOKEN.fullmatch(str(host.get("version", ""))) is None
        or host.get("version_source") != "observed-cli"
    ):
        errors.append("host observation is invalid")
    environment = value.get("environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != ENVIRONMENT_KEYS
        or environment.get("os") not in {"windows", "linux", "macos"}
        or environment.get("architecture") not in {"x86_64", "arm64"}
    ):
        errors.append("environment summary is invalid")
    return errors


def _project_errors(value: dict[str, Any]) -> list[str]:
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != PROJECT_KEYS:
        return ["project summary keys are invalid"]
    project_types = project.get("types")
    workspace_count = project.get("workspace_count")
    if (
        common.SHA256.fullmatch(str(project.get("identity_sha256", ""))) is None
        or project.get("distinct_from_divan") is not True
        or common.SHA256.fullmatch(
            str(project.get("distinctness_policy_sha256", ""))
        ) is None
        or not isinstance(project_types, list)
        or project_types != sorted(set(project_types))
        or not project_types
        or not all(item in PROJECT_TYPES for item in project_types)
        or type(workspace_count) is not int
        or workspace_count <= 0
    ):
        return ["project summary is invalid or project is not distinct from Divan"]
    return []


def _goal_errors(value: dict[str, Any]) -> list[str]:
    goal = value.get("goal")
    if not isinstance(goal, dict) or set(goal) != GOAL_KEYS:
        return ["goal evidence keys are invalid"]
    artifacts = goal.get("artifact_sha256")
    if (
        goals.GOAL_ID_PATTERN.fullmatch(str(goal.get("id", ""))) is None
        or goal.get("state") not in VERIFIED_STATES
        or goal.get("target") not in receipts.TARGETS
        or common.SHA256.fullmatch(str(goal.get("receipt_sha256", ""))) is None
        or not isinstance(artifacts, list)
        or not artifacts
        or artifacts != sorted(set(artifacts))
        or not all(common.SHA256.fullmatch(str(item)) for item in artifacts)
    ):
        return ["goal evidence is invalid"]
    return []


def _check_token_errors(check: dict[str, Any], label: str) -> list[str]:
    if (
        common.SHA256.fullmatch(str(check.get("workspace_sha256", ""))) is None
        or common.SAFE_TOKEN.fullmatch(str(check.get("runner", ""))) is None
        or common.SAFE_TOKEN.fullmatch(str(check.get("name", ""))) is None
        or common.SHA256.fullmatch(str(check.get("argv_sha256", ""))) is None
        or common.SHA256.fullmatch(
            str(check.get("timeout_policy_sha256", ""))
        ) is None
        or common.SHA256.fullmatch(str(check.get("output_sha256", ""))) is None
    ):
        return [f"{label} contains an invalid token or hash"]
    return []


def _one_check_errors(
    check: object, index: int
) -> tuple[list[str], str | None, bool]:
    label = f"checks[{index}]"
    if not isinstance(check, dict) or set(check) != CHECK_KEYS:
        return [f"{label} keys are invalid"], None, False
    errors: list[str] = []
    identifier = check.get("id")
    check_class = check.get("class")
    duration = _exact_integer(check.get("duration_ms"), f"{label}.duration_ms", errors)
    timeout = _exact_integer(check.get("timeout_ms"), f"{label}.timeout_ms", errors)
    exit_code = _exact_integer(check.get("exit_code"), f"{label}.exit_code", errors)
    if not isinstance(identifier, str) or CHECK_ID.fullmatch(identifier) is None:
        errors.append(f"{label}.id is invalid")
        identifier = None
    if check_class not in CHECK_CLASSES:
        errors.append(f"{label}.class is invalid")
    errors.extend(_check_token_errors(check, label))
    if check.get("status") != "passed" or exit_code != 0:
        errors.append(f"{label} must be a passed check with exit code zero")
    if (
        duration is not None
        and timeout is not None
        and (duration < 0 or timeout <= 0 or duration > timeout)
    ):
        errors.append(f"{label} duration/timeout is invalid")
    return errors, identifier, check_class in TEST_CLASSES


def _check_errors(value: dict[str, Any]) -> list[str]:
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks or len(checks) > 8:
        return ["checks must contain between one and eight entries"]
    errors: list[str] = []
    identifiers: list[str] = []
    has_test = False
    for index, check in enumerate(checks):
        row_errors, identifier, is_test = _one_check_errors(check, index)
        errors.extend(row_errors)
        if identifier is not None:
            identifiers.append(identifier)
        has_test = has_test or is_test
    if identifiers != sorted(set(identifiers)):
        errors.append("checks must have unique IDs in canonical order")
    if not has_test:
        errors.append("checks must include at least one test-class check")
    return errors


def _proof_errors(value: dict[str, Any]) -> list[str]:
    proof = value.get("proof")
    if not isinstance(proof, dict) or set(proof) != PROOF_KEYS:
        return ["proof keys are invalid"]
    errors: list[str] = []
    if PROOF_ID.fullmatch(str(proof.get("id", ""))) is None:
        errors.append("proof.id is invalid")
    started = _timestamp(proof.get("started_at"), "proof.started_at", errors)
    completed = _timestamp(proof.get("completed_at"), "proof.completed_at", errors)
    if started is not None and completed is not None and completed < started:
        errors.append("proof completion precedes its start")
    if proof.get("source_stable") is not True:
        errors.append("proof source was not stable")
    digest = proof.get("receipt_digest")
    if common.SHA256.fullmatch(str(digest or "")) is None:
        errors.append("proof receipt digest is invalid")
    elif digest != common.digest_schema_2(value):
        errors.append("proof receipt digest does not match")
    return errors


def errors(value: dict[str, Any]) -> list[str]:
    result: list[str] = []
    if set(value) != RECEIPT_KEYS:
        result.append("schema 2 adoption receipt keys are invalid")
    if value.get("schema_version") != 2 or value.get("product") != "divan-clean-room-adoption":
        result.append("schema 2 adoption receipt identity is invalid")
    result.extend(_source_errors(value))
    result.extend(_host_environment_errors(value))
    operator = value.get("operator")
    if (
        not isinstance(operator, dict)
        or set(operator) != OPERATOR_KEYS
        or operator.get("role") not in OPERATOR_ROLES
    ):
        result.append("operator role is invalid")
    result.extend(_project_errors(value))
    result.extend(_goal_errors(value))
    result.extend(_check_errors(value))
    result.extend(_proof_errors(value))
    return result


def build(
    *,
    divan: dict[str, object],
    host: dict[str, object],
    environment: dict[str, object],
    operator: dict[str, object],
    project: dict[str, object],
    goal: dict[str, object],
    checks: list[dict[str, object]],
    proof: dict[str, object],
) -> dict[str, object]:
    value: dict[str, Any] = {
        "schema_version": 2,
        "product": "divan-clean-room-adoption",
        "divan": copy.deepcopy(divan),
        "host": copy.deepcopy(host),
        "environment": copy.deepcopy(environment),
        "operator": copy.deepcopy(operator),
        "project": copy.deepcopy(project),
        "goal": copy.deepcopy(goal),
        "checks": copy.deepcopy(checks),
        "proof": {**copy.deepcopy(proof), "receipt_digest": ""},
    }
    proof_value = cast(dict[str, Any], value["proof"])
    proof_value["receipt_digest"] = common.digest_schema_2(value)
    validation_errors = errors(value) + common.privacy_errors(value)
    if validation_errors:
        raise ValueError("; ".join(sorted(set(validation_errors))))
    return value
