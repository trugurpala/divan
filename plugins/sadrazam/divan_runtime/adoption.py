"""Privacy-bounded adoption receipts for the Divan Project Contract."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import platform
import re
from datetime import datetime
from typing import Any, cast

from . import goals, project_state, receipts

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
SCHEMA_2_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "product",
        "divan",
        "host",
        "environment",
        "operator",
        "project",
        "goal",
        "checks",
        "proof",
    }
)
DIVAN_KEYS = frozenset({"version", "ref", "commit"})
SCHEMA_2_DIVAN_KEYS = frozenset(
    {"version", "ref", "commit", "distribution", "runner_sha256"}
)
HOST_KEYS = frozenset({"name", "version"})
SCHEMA_2_HOST_KEYS = frozenset({"name", "version", "version_source"})
ENVIRONMENT_KEYS = frozenset({"os", "architecture"})
PROJECT_KEYS = frozenset({"identity_sha256", "types", "workspace_count"})
SCHEMA_2_PROJECT_KEYS = frozenset(
    {
        "identity_sha256",
        "distinct_from_divan",
        "distinctness_policy_sha256",
        "types",
        "workspace_count",
    }
)
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
SCHEMA_2_GOAL_KEYS = frozenset(
    {
        "id",
        "state",
        "target",
        "receipt_sha256",
        "artifact_sha256",
    }
)
CHECK_KEYS = frozenset({"status", "evidence_hashes"})
SCHEMA_2_CHECK_KEYS = frozenset(
    {
        "id",
        "class",
        "workspace_sha256",
        "runner",
        "name",
        "argv_sha256",
        "status",
        "exit_code",
        "duration_ms",
        "timeout_ms",
        "timeout_policy_sha256",
        "output_sha256",
    }
)
DECLARATION_KEYS = frozenset({"submitter"})
OPERATOR_KEYS = frozenset({"role"})
PROOF_KEYS = frozenset(
    {
        "id",
        "started_at",
        "completed_at",
        "source_stable",
        "receipt_digest",
    }
)
PROJECT_TYPES = frozenset(
    {"application", "documentation", "library", "monorepo", "public-web", "service"}
)
QUALIFYING_HOSTS = frozenset({"claude-code", "codex"})
OPERATOR_ROLES = frozenset({"maintainer", "external"})
CHECK_CLASSES = frozenset({"test", "regression", "typecheck", "check", "lint", "build"})
TEST_CLASSES = frozenset({"test", "regression"})
PROOF_ID = re.compile(r"^proof-[0-9a-f]{12}$")
CHECK_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}:[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
)
RFC3339_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
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


def _digest_schema_2(value: dict[str, Any]) -> str:
    """Digest schema 2 while excluding only its self-referential digest."""
    material = copy.deepcopy(value)
    proof = material.get("proof")
    if isinstance(proof, dict):
        proof.pop("receipt_digest", None)
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


def serialize_adoption_json(value: dict[str, object]) -> bytes:
    """Serialize one already verified adoption receipt."""
    return _json_bytes(value)


def serialize_adoption_markdown(value: dict[str, object]) -> bytes:
    """Render a human-readable wrapper with the canonical JSON envelope."""
    if value.get("schema_version") == 1:
        return _markdown(value)
    proof = value.get("proof")
    host = value.get("host")
    goal = value.get("goal")
    operator = value.get("operator")
    if not all(isinstance(item, dict) for item in (proof, host, goal, operator)):
        raise ValueError("schema 2 adoption receipt is incomplete")
    proof_value = cast(dict[str, Any], proof)
    host_value = cast(dict[str, Any], host)
    goal_value = cast(dict[str, Any], goal)
    operator_value = cast(dict[str, Any], operator)
    body = (
        "# Divan Clean-Room Adoption Receipt\n\n"
        f"- Status: `{goal_value['state']}`\n"
        f"- Host: `{host_value['name']} {host_value['version']}`\n"
        f"- Operator role: `{operator_value['role']}`\n"
        f"- Proof: `{proof_value['id']}`\n"
        f"- Receipt: `{proof_value['receipt_digest']}`\n\n"
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
    """Build deterministic JSON and Markdown receipts without writing files."""
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
    return {
        "schema_version": 1,
        "status": (
            "valid-schema-1-owner-canary"
            if submitter == "maintainer"
            else "valid-schema-1-independent-declaration"
        ),
        "json": _json_bytes(value).decode("utf-8"),
        "markdown": _markdown(value).decode("utf-8"),
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


def _schema_2_source_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    divan = value.get("divan")
    if not isinstance(divan, dict) or set(divan) != SCHEMA_2_DIVAN_KEYS:
        return ["Divan source keys are invalid"]
    version = divan.get("version")
    if (
        not isinstance(version, str)
        or project_state.SEMVER.fullmatch(version) is None
        or divan.get("ref") != f"v{version}"
        or HEX_40.fullmatch(str(divan.get("commit", ""))) is None
        or divan.get("distribution") != "immutable-release"
        or SHA256.fullmatch(str(divan.get("runner_sha256", ""))) is None
    ):
        errors.append("Divan source identity is invalid")
    return errors


def _schema_2_host_errors(value: dict[str, Any]) -> list[str]:
    host = value.get("host")
    if (
        not isinstance(host, dict)
        or set(host) != SCHEMA_2_HOST_KEYS
        or host.get("name") not in QUALIFYING_HOSTS
        or SAFE_TOKEN.fullmatch(str(host.get("version", ""))) is None
        or host.get("version_source") != "observed-cli"
    ):
        return ["host observation is invalid"]
    return []


def _schema_2_environment_errors(value: dict[str, Any]) -> list[str]:
    environment = value.get("environment")
    if (
        not isinstance(environment, dict)
        or set(environment) != ENVIRONMENT_KEYS
        or environment.get("os") not in {"windows", "linux", "macos"}
        or environment.get("architecture") not in {"x86_64", "arm64"}
    ):
        return ["environment summary is invalid"]
    return []


def _schema_2_project_errors(value: dict[str, Any]) -> list[str]:
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != SCHEMA_2_PROJECT_KEYS:
        return ["project summary keys are invalid"]
    project_types = project.get("types")
    workspace_count = project.get("workspace_count")
    if (
        SHA256.fullmatch(str(project.get("identity_sha256", ""))) is None
        or project.get("distinct_from_divan") is not True
        or SHA256.fullmatch(
            str(project.get("distinctness_policy_sha256", ""))
        )
        is None
        or not isinstance(project_types, list)
        or project_types != sorted(set(project_types))
        or not project_types
        or not all(item in PROJECT_TYPES for item in project_types)
        or type(workspace_count) is not int
        or workspace_count <= 0
    ):
        return ["project summary is invalid or project is not distinct from Divan"]
    return []


def _schema_2_goal_errors(value: dict[str, Any]) -> list[str]:
    goal = value.get("goal")
    if not isinstance(goal, dict) or set(goal) != SCHEMA_2_GOAL_KEYS:
        return ["goal evidence keys are invalid"]
    artifacts = goal.get("artifact_sha256")
    if (
        goals.GOAL_ID_PATTERN.fullmatch(str(goal.get("id", ""))) is None
        or goal.get("state") not in VERIFIED_STATES
        or goal.get("target") not in receipts.TARGETS
        or SHA256.fullmatch(str(goal.get("receipt_sha256", ""))) is None
        or not isinstance(artifacts, list)
        or not artifacts
        or artifacts != sorted(set(artifacts))
        or not all(SHA256.fullmatch(str(item)) for item in artifacts)
    ):
        return ["goal evidence is invalid"]
    return []


def _schema_2_check_errors(value: dict[str, Any]) -> list[str]:
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks or len(checks) > 8:
        return ["checks must contain between one and eight entries"]
    errors: list[str] = []
    identifiers: list[str] = []
    has_test = False
    for index, check in enumerate(checks):
        label = f"checks[{index}]"
        if not isinstance(check, dict) or set(check) != SCHEMA_2_CHECK_KEYS:
            errors.append(f"{label} keys are invalid")
            continue
        identifier = check.get("id")
        check_class = check.get("class")
        duration = _exact_integer(
            check.get("duration_ms"), f"{label}.duration_ms", errors
        )
        timeout = _exact_integer(
            check.get("timeout_ms"), f"{label}.timeout_ms", errors
        )
        exit_code = _exact_integer(
            check.get("exit_code"), f"{label}.exit_code", errors
        )
        if not isinstance(identifier, str) or CHECK_ID.fullmatch(identifier) is None:
            errors.append(f"{label}.id is invalid")
        else:
            identifiers.append(identifier)
        if check_class not in CHECK_CLASSES:
            errors.append(f"{label}.class is invalid")
        elif check_class in TEST_CLASSES:
            has_test = True
        if (
            SHA256.fullmatch(str(check.get("workspace_sha256", ""))) is None
            or SAFE_TOKEN.fullmatch(str(check.get("runner", ""))) is None
            or SAFE_TOKEN.fullmatch(str(check.get("name", ""))) is None
            or SHA256.fullmatch(str(check.get("argv_sha256", ""))) is None
            or SHA256.fullmatch(
                str(check.get("timeout_policy_sha256", ""))
            )
            is None
            or SHA256.fullmatch(str(check.get("output_sha256", ""))) is None
        ):
            errors.append(f"{label} contains an invalid token or hash")
        if check.get("status") != "passed" or exit_code != 0:
            errors.append(f"{label} must be a passed check with exit code zero")
        if (
            duration is not None
            and timeout is not None
            and (duration < 0 or timeout <= 0 or duration > timeout)
        ):
            errors.append(f"{label} duration/timeout is invalid")
    if identifiers != sorted(set(identifiers)):
        errors.append("checks must have unique IDs in canonical order")
    if not has_test:
        errors.append("checks must include at least one test-class check")
    return errors


def _schema_2_proof_errors(value: dict[str, Any]) -> list[str]:
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
    if SHA256.fullmatch(str(digest or "")) is None:
        errors.append("proof receipt digest is invalid")
    elif digest != _digest_schema_2(value):
        errors.append("proof receipt digest does not match")
    return errors


def _schema_2_errors(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(value) != SCHEMA_2_RECEIPT_KEYS:
        errors.append("schema 2 adoption receipt keys are invalid")
    if (
        value.get("schema_version") != 2
        or value.get("product") != "divan-clean-room-adoption"
    ):
        errors.append("schema 2 adoption receipt identity is invalid")
    errors.extend(_schema_2_source_errors(value))
    errors.extend(_schema_2_host_errors(value))
    errors.extend(_schema_2_environment_errors(value))
    operator = value.get("operator")
    if (
        not isinstance(operator, dict)
        or set(operator) != OPERATOR_KEYS
        or operator.get("role") not in OPERATOR_ROLES
    ):
        errors.append("operator role is invalid")
    errors.extend(_schema_2_project_errors(value))
    errors.extend(_schema_2_goal_errors(value))
    errors.extend(_schema_2_check_errors(value))
    errors.extend(_schema_2_proof_errors(value))
    return errors


def _verify_schema_1(value: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
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
            else "valid-schema-1-owner-canary"
            if submitter == "maintainer"
            else "valid-schema-1-independent-declaration"
        ),
        "eligible_for_v1": False,
        "errors": sorted(set(errors)),
    }


def verify_adoption_value(
    value: dict[str, object], *, document_text: str | None = None
) -> dict[str, object]:
    """Verify one in-memory schema-1 or schema-2 adoption receipt."""
    if not isinstance(value, dict):
        return {
            "schema_version": 0,
            "status": "invalid",
            "eligible_for_v1": False,
            "errors": ["adoption receipt root must be an object"],
        }
    if value.get("schema_version") == 1:
        result = _verify_schema_1(value)
    elif value.get("schema_version") == 2:
        errors = _schema_2_errors(value)
        errors.extend(_privacy_errors(value))
        result = {
            "schema_version": 2,
            "status": "invalid" if errors else "valid-clean-room-adoption",
            "eligible_for_v1": not errors,
            "errors": sorted(set(errors)),
        }
    else:
        result = {
            "schema_version": value.get("schema_version", 0),
            "status": "invalid",
            "eligible_for_v1": False,
            "errors": ["adoption receipt schema is unsupported"],
        }
    if document_text is not None:
        document_errors = _privacy_errors(document_text, "document")
        if document_errors:
            result["status"] = "invalid"
            result["eligible_for_v1"] = False
            result["errors"] = sorted(
                set(result.get("errors", [])) | set(document_errors)
            )
    return result


def build_clean_room_receipt(
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
    """Build and verify one canonical schema-2 clean-room receipt."""
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
    proof_value["receipt_digest"] = _digest_schema_2(value)
    result = verify_adoption_value(value)
    if not result["eligible_for_v1"]:
        result_errors = cast(list[object], result["errors"])
        raise ValueError("; ".join(str(item) for item in result_errors))
    return value


def verify_adoption(path: pathlib.Path | str) -> dict[str, Any]:
    """Verify receipt schema, digest, privacy, and technical eligibility."""
    receipt_path = pathlib.Path(path)
    try:
        raw_text = receipt_path.read_text(encoding="utf-8")
        value = _read_receipt(receipt_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {
            "schema_version": 0,
            "status": "invalid",
            "eligible_for_v1": False,
            "errors": [str(error)],
        }
    return verify_adoption_value(value, document_text=raw_text)
