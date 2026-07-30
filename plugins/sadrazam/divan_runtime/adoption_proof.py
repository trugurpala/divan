"""Bounded planning and execution support for clean-room adoption proofs."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from collections.abc import Callable
from datetime import datetime
from typing import Any

from . import (
    adoption,
    adoption_proof_common,
    adoption_runner,
    engine,
    execution,
    goals,
    project_state,
    receipts,
    timeouts,
)

QUALIFYING_HOSTS = adoption_proof_common.QUALIFYING_HOSTS
OPERATOR_ROLES = frozenset({"maintainer", "external"})
NODE_MANAGERS = frozenset({"bun", "npm", "pnpm", "yarn"})
MAX_CHECKS = 8
DISTINCTNESS_POLICY = {
    "version": 1,
    "complete_signature": [
        "VERSION",
        ".claude-plugin/marketplace.json:name=divan",
        "plugins/sadrazam/divan_runtime/modules.json",
    ],
    "partial_signature": "blocked",
}
CHECK_PRIORITY = {
    "test": 0,
    "regression": 1,
    "typecheck": 2,
    "check": 3,
    "lint": 4,
    "build": 5,
}


_canonical_bytes = adoption_proof_common.canonical_bytes
_hash_bytes = adoption_proof_common.hash_bytes
_domain_hash = adoption_proof_common.domain_hash


def _real_directory(path: pathlib.Path | str, label: str) -> pathlib.Path:
    candidate = pathlib.Path(path)
    if project_state._is_reparse_or_symlink(candidate):
        raise ValueError(f"{label} uses a symlink or reparse point")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} is unavailable: {error}") from error
    if not resolved.is_dir():
        raise ValueError(f"{label} must be a directory")
    if project_state._is_reparse_or_symlink(resolved):
        raise ValueError(f"{label} uses a symlink or reparse point")
    return resolved


def _bounded_json(path: pathlib.Path, label: str) -> dict[str, Any]:
    if project_state._is_reparse_or_symlink(path):
        raise ValueError(f"{label} uses a symlink or reparse point")
    try:
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise ValueError(f"{label} is unavailable or too large")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is invalid: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain an object")
    return value


def classify_distinct_project(root: pathlib.Path | str) -> dict[str, Any]:
    """Reject complete and ambiguous partial Divan source signatures."""
    project = _real_directory(root, "project")
    version_path = project / "VERSION"
    marketplace_path = project / ".claude-plugin" / "marketplace.json"
    modules_path = (
        project / "plugins" / "sadrazam" / "divan_runtime" / "modules.json"
    )
    version_marker = version_path.exists()
    marketplace_marker = marketplace_path.exists()
    modules_marker = modules_path.exists()
    if version_marker and project_state._is_reparse_or_symlink(version_path):
        raise ValueError("partial Divan signature uses an unsafe VERSION marker")
    if modules_marker and project_state._is_reparse_or_symlink(modules_path):
        raise ValueError("partial Divan signature uses an unsafe modules marker")
    marketplace_is_divan = False
    if marketplace_marker:
        marketplace = _bounded_json(marketplace_path, "Divan marketplace marker")
        marketplace_is_divan = marketplace.get("name") == "divan"
        if not marketplace_is_divan:
            raise ValueError("partial Divan signature has an ambiguous marketplace")
    markers = (version_marker, marketplace_is_divan, modules_marker)
    count = sum(markers)
    if count == len(markers):
        raise ValueError("project is the Divan source tree")
    if count:
        raise ValueError("partial Divan signature is ambiguous")
    return {
        "distinct": True,
        "policy_sha256": _domain_hash(
            "divan-distinct-project-policy-v1", DISTINCTNESS_POLICY
        ),
    }


def safe_argv(
    command: dict[str, Any], *, python_executable: str = sys.executable
) -> tuple[str, ...]:
    """Construct argv from bounded discovery fields without a shell."""
    manager = command.get("manager")
    name = command.get("name")
    if (
        not isinstance(manager, str)
        or not isinstance(name, str)
        or engine.PACKAGE_SCRIPT_NAME.fullmatch(name) is None
    ):
        raise ValueError("project command has an unsafe manager or script name")
    if manager in NODE_MANAGERS:
        return (manager, "run", name)
    if manager == "python" and name == "test":
        return (python_executable, "-m", "unittest", "discover")
    if manager == "go" and name == "test":
        return ("go", "test", "./...")
    if manager == "cargo" and name == "test":
        return ("cargo", "test")
    raise ValueError("project command runner is unsupported")


def _check_class(name: str) -> str | None:
    normalized = name.casefold()
    if normalized == "test" or normalized.startswith("test:"):
        return "test"
    if normalized == "regression" or normalized.startswith("regression:"):
        return "regression"
    if normalized in {"typecheck", "check", "lint", "build"}:
        return normalized
    return None


def _workspace(
    root: pathlib.Path, relative: object
) -> tuple[pathlib.Path, str]:
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("workspace path is invalid")
    pure = pathlib.PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError("workspace path escapes the project")
    candidate = root.joinpath(*pure.parts)
    if project_state._is_reparse_or_symlink(candidate):
        raise ValueError("workspace uses a symlink or reparse point")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("workspace escapes the project") from error
    if not resolved.is_dir():
        raise ValueError("workspace must be a directory")
    normalized = "." if relative in {"", "."} else pure.as_posix()
    return resolved, normalized


def _check_identifier(workspace: str, name: str) -> str:
    prefix = (
        "root"
        if workspace == "."
        else "ws-" + _domain_hash("divan-workspace-v1", workspace)[7:19]
    )
    safe_name = name.replace(":", "-")
    return f"{prefix}:{safe_name}"


def select_checks(
    inspection: dict[str, Any],
    goal_route: dict[str, Any],
    root: pathlib.Path,
) -> list[dict[str, Any]]:
    """Select at most eight deterministic, test-backed discovered commands."""
    required_commands = adoption_proof_common.required_commands(goal_route)
    conflicts = inspection.get("package_manager_conflicts")
    if not isinstance(conflicts, list) or conflicts:
        raise ValueError("package manager evidence is ambiguous")
    commands = inspection.get("commands")
    if not isinstance(commands, list):
        raise ValueError("project command discovery is invalid")
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    policy_digest = adoption_proof_common.timeout_policy_digest()
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError("project command discovery is invalid")
        check_class = _check_class(str(command.get("name", "")))
        if check_class is None:
            continue
        workspace_path, workspace = _workspace(root, command.get("workspace"))
        manager = command.get("manager")
        name = command.get("name")
        if not isinstance(manager, str) or not isinstance(name, str):
            raise ValueError("project command fields are invalid")
        identity = (workspace, manager, name)
        if identity in seen:
            continue
        seen.add(identity)
        argv = safe_argv(command)
        timeout_class = adoption_proof_common.timeout_class(check_class)
        decision = timeouts.resolve_default(timeout_class)
        candidates.append(
            {
                "id": _check_identifier(workspace, name),
                "class": check_class,
                "workspace": workspace,
                "workspace_path": workspace_path,
                "workspace_sha256": _domain_hash(
                    "divan-workspace-v1", workspace
                ),
                "runner": manager,
                "name": name,
                "goal_required": command.get("command") in required_commands,
                "argv": argv,
                "argv_sha256": _domain_hash(
                    "divan-check-argv-v1", list(argv)
                ),
                "timeout_class": timeout_class,
                "timeout_ms": decision.configured_seconds * 1000,
                "timeout_policy_sha256": policy_digest,
            }
        )
    candidates.sort(
        key=lambda row: (
            0 if row["goal_required"] else 1,
            0 if row["workspace"] == "." else 1,
            CHECK_PRIORITY[row["class"]],
            row["workspace"],
            row["runner"],
            row["name"],
        )
    )
    if adoption_proof_common.missing_required_commands(
        required_commands, commands, candidates
    ):
        raise ValueError(
            "goal route requires unavailable or unsupported project checks"
        )
    adoption_proof_common.enforce_check_capacity(candidates, MAX_CHECKS)
    selected = candidates[:MAX_CHECKS]
    if not any(row["class"] in adoption.TEST_CLASSES for row in selected):
        raise ValueError("proof plan requires at least one test-class check")
    selected.sort(key=lambda row: row["id"])
    return selected


def build_proof_plan(
    project: pathlib.Path | str,
    goal_id: str,
    host: str,
    operator_role: str = "maintainer",
    *,
    runner_path: pathlib.Path | None = None,
    expected_runner_sha256: str | None = None,
) -> dict[str, Any]:
    """Build a complete read-only clean-room proof preview."""
    root = _real_directory(project, "project")
    if host not in QUALIFYING_HOSTS:
        raise ValueError("host does not have a qualifying observed-version contract")
    if operator_role not in OPERATOR_ROLES:
        raise ValueError("operator role must be maintainer or external")
    distinct = classify_distinct_project(root)
    state, state_errors = project_state.load_install_state(root)
    if state is None or state_errors:
        raise ValueError(
            "Divan install state is invalid: " + "; ".join(state_errors)
        )
    source = state["installed"]
    version = source["version"]
    if source["source_ref"] != f"v{version}":
        raise ValueError("clean-room proof requires an immutable release")
    if source["source_commit"] == "0" * 40:
        raise ValueError("clean-room proof source commit is invalid")
    spec_root, _evidence, receipt_path = goals._goal_paths(root, goal_id)
    goal_verification = receipts.verify_receipt(receipt_path)
    if (
        not goal_verification.get("ok")
        or goal_verification.get("state") not in adoption.VERIFIED_STATES
        or not goal_verification.get("artifacts")
    ):
        raise ValueError("goal receipt must be valid, verified, and artifact-backed")
    goal_receipt = _bounded_json(receipt_path, "goal receipt")
    inspection = goals._inspection(root)
    goal_route = _bounded_json(spec_root / "route.json", "goal route")
    checks = select_checks(inspection, goal_route, root)
    candidate = pathlib.Path(sys.argv[0]) if runner_path is None else runner_path
    resolved_runner, runner_sha256 = adoption_runner.verify(
        candidate,
        source,
        expected_digest=expected_runner_sha256,
    )
    public_checks = [
        {
            key: value
            for key, value in row.items()
            if key not in {"workspace_path", "goal_required"}
        }
        for row in checks
    ]
    proof_seed = {
        "source": source,
        "runner_sha256": runner_sha256,
        "host": host,
        "operator_role": operator_role,
        "project_identity": state["project_identity"],
        "goal_id": goal_id,
        "goal_receipt_sha256": _hash_bytes(receipt_path.read_bytes()),
        "checks": [
            {
                key: value
                for key, value in row.items()
                if key not in {"workspace_path", "argv", "goal_required"}
            }
            for row in checks
        ],
        "distinctness_policy_sha256": distinct["policy_sha256"],
    }
    proof_id = "proof-" + hashlib.sha256(
        _canonical_bytes(proof_seed)
    ).hexdigest()[:12]
    return {
        "schema_version": 1,
        "status": "ready",
        "proof_id": proof_id,
        "divan": {
            "version": version,
            "ref": source["source_ref"],
            "commit": source["source_commit"],
            "distribution": "immutable-release",
            "runner_sha256": runner_sha256,
        },
        "host_probe": {
            "argv": QUALIFYING_HOSTS[host],
            "status": "planned",
        },
        "operator": {"role": operator_role},
        "environment": adoption._coarse_environment(),
        "project": {
            "identity_sha256": state["project_identity"],
            "distinct_from_divan": distinct["distinct"],
            "distinctness_policy_sha256": distinct["policy_sha256"],
            "types": inspection["project_types"],
            "workspace_count": len(inspection["workspaces"]),
        },
        "goal": {
            "id": goal_id,
            "state": goal_verification["state"],
            "target": goal_receipt["target"],
            "receipt_sha256": _hash_bytes(receipt_path.read_bytes()),
            "artifact_sha256": sorted(
                "sha256:" + digest
                for digest in goal_verification["artifacts"].values()
            ),
        },
        "checks": public_checks,
        "writes": [
            f".divan/adoption/.staging/{proof_id}/",
            f".divan/adoption/{proof_id}/",
        ],
        "plan_digest": _domain_hash("divan-clean-room-plan-v1", proof_seed),
        "_private": {
            "root": root,
            "runner_path": resolved_runner,
            "receipt_path": receipt_path,
            "host": host,
            "checks": checks,
        },
    }


from . import adoption_proof_execution  # noqa: E402


def execute_proof(
    plan: dict[str, Any],
    *,
    command_runner: Callable[..., execution.ExecutionResult] = execution.run,
    clock: Callable[[], datetime] = adoption_proof_common.utc_now,
) -> dict[str, Any]:
    """Execute one proof plan once and promote only offline-verified evidence."""
    return adoption_proof_execution.execute_proof(
        plan,
        plan_builder=build_proof_plan,
        command_runner=command_runner,
        clock=clock,
    )
