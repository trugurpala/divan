"""Bounded planning and execution support for clean-room adoption proofs."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, cast

from . import adoption, engine, execution, goals, project_state, receipts, timeouts

QUALIFYING_HOSTS = {
    "claude-code": ("claude", "--version"),
    "codex": ("codex", "--version"),
}
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


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _domain_hash(domain: str, value: object) -> str:
    return _hash_bytes(domain.encode("utf-8") + b"\0" + _canonical_bytes(value))


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


def _timeout_class(check_class: str) -> str:
    if check_class in adoption.TEST_CLASSES:
        return "test"
    if check_class == "build":
        return "verify"
    return "fast-check"


def _timeout_policy_digest() -> str:
    policy = timeouts.DATA_DIRECTORY / "timeout-policy.json"
    return _hash_bytes(policy.read_bytes())


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
    goal_receipt: dict[str, Any],
    root: pathlib.Path,
) -> list[dict[str, Any]]:
    """Select at most eight deterministic, test-backed discovered commands."""
    del goal_receipt  # Goal authority is validated separately; no shell text is read.
    conflicts = inspection.get("package_manager_conflicts")
    if not isinstance(conflicts, list) or conflicts:
        raise ValueError("package manager evidence is ambiguous")
    commands = inspection.get("commands")
    if not isinstance(commands, list):
        raise ValueError("project command discovery is invalid")
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    policy_digest = _timeout_policy_digest()
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
        timeout_class = _timeout_class(check_class)
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
            0 if row["workspace"] == "." else 1,
            CHECK_PRIORITY[row["class"]],
            row["workspace"],
            row["runner"],
            row["name"],
        )
    )
    selected = candidates[:MAX_CHECKS]
    if not any(row["class"] in adoption.TEST_CLASSES for row in selected):
        raise ValueError("proof plan requires at least one test-class check")
    selected.sort(key=lambda row: row["id"])
    return selected


def _runner_digest(path: pathlib.Path | None) -> tuple[pathlib.Path, str]:
    candidate = pathlib.Path(sys.argv[0]) if path is None else pathlib.Path(path)
    if project_state._is_reparse_or_symlink(candidate):
        raise ValueError("Divan project runner uses a symlink or reparse point")
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file() or resolved.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("Divan project runner is unavailable or too large")
        return resolved, _hash_bytes(resolved.read_bytes())
    except OSError as error:
        raise ValueError(f"Divan project runner is unavailable: {error}") from error


def build_proof_plan(
    project: pathlib.Path | str,
    goal_id: str,
    host: str,
    operator_role: str = "maintainer",
    *,
    runner_path: pathlib.Path | None = None,
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
    _spec, _evidence, receipt_path = goals._goal_paths(root, goal_id)
    goal_verification = receipts.verify_receipt(receipt_path)
    if (
        not goal_verification.get("ok")
        or goal_verification.get("state") not in adoption.VERIFIED_STATES
        or not goal_verification.get("artifacts")
    ):
        raise ValueError("goal receipt must be valid, verified, and artifact-backed")
    goal_receipt = _bounded_json(receipt_path, "goal receipt")
    inspection = goals._inspection(root)
    checks = select_checks(inspection, goal_receipt, root)
    resolved_runner, runner_sha256 = _runner_digest(runner_path)
    public_checks = [
        {
            key: value
            for key, value in row.items()
            if key not in {"workspace_path"}
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
                if key not in {"workspace_path", "argv"}
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
        "writes": [f".divan/adoption/{proof_id}/"],
        "plan_digest": _domain_hash("divan-clean-room-plan-v1", proof_seed),
        "_private": {
            "root": root,
            "runner_path": resolved_runner,
            "receipt_path": receipt_path,
            "host": host,
            "checks": checks,
        },
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("proof clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_journal(path: pathlib.Path, value: dict[str, Any]) -> None:
    receipts._atomic_json(path, value)


def _source_fingerprint(plan: dict[str, Any]) -> str:
    private = plan["_private"]
    root = private["root"]
    check_rows = private["checks"]
    workspaces = sorted(
        {row["workspace_path"] for row in check_rows},
        key=lambda item: item.as_posix(),
    )
    markers = (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "go.mod",
        "Cargo.toml",
    )
    files: set[pathlib.Path] = {
        root / ".divan" / "config.json",
        root / ".divan" / "install-state.json",
        private["receipt_path"],
    }
    for workspace in workspaces:
        for marker in markers:
            candidate = workspace / marker
            if candidate.exists():
                files.add(candidate)
    rows: list[dict[str, str]] = []
    for path in sorted(files, key=lambda item: item.as_posix()):
        if project_state._is_reparse_or_symlink(path):
            raise ValueError("proof identity input uses a symlink or reparse point")
        resolved = path.resolve(strict=True)
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as error:
            raise ValueError("proof identity input escapes the project") from error
        if not resolved.is_file() or resolved.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("proof identity input is unavailable or too large")
        rows.append(
            {
                "path_sha256": _domain_hash(
                    "divan-proof-identity-path-v1", relative
                ),
                "content_sha256": _hash_bytes(resolved.read_bytes()),
            }
        )
    return _domain_hash("divan-proof-source-fingerprint-v1", rows)


def _host_version(result: execution.ExecutionResult) -> str:
    if result.status != "PASS" or result.returncode != 0:
        raise ValueError("host version probe did not pass")
    tokens = result.stdout.replace("\r", " ").replace("\n", " ").split()
    candidates = [
        token.removeprefix("v")
        for token in tokens
        if any(character.isdigit() for character in token)
        and adoption.SAFE_TOKEN.fullmatch(token.removeprefix("v")) is not None
    ]
    if len(candidates) != 1:
        raise ValueError("host version probe output is ambiguous")
    return candidates[0]


def _result_status(result: execution.ExecutionResult) -> str:
    if result.status == "PASS" and result.returncode == 0:
        return "passed"
    if result.status == "TIMEOUT":
        return "timed-out"
    if result.status == "CANCELLED":
        return "cancelled"
    return "failed"


def _public_check_result(
    row: dict[str, Any], result: execution.ExecutionResult
) -> dict[str, Any]:
    duration_ms = max(0, round(result.elapsed_seconds * 1000))
    duration_ms = min(duration_ms, row["timeout_ms"])
    return {
        "id": row["id"],
        "class": row["class"],
        "workspace_sha256": row["workspace_sha256"],
        "runner": row["runner"],
        "name": row["name"],
        "argv_sha256": row["argv_sha256"],
        "status": _result_status(result),
        "exit_code": result.returncode,
        "duration_ms": duration_ms,
        "timeout_ms": row["timeout_ms"],
        "timeout_policy_sha256": row["timeout_policy_sha256"],
        "output_sha256": _domain_hash(
            "divan-proof-output-v1",
            {"stdout": result.stdout, "stderr": result.stderr},
        ),
    }


def _failure_result(
    plan: dict[str, Any], journal: dict[str, Any], status: str, reason: str
) -> dict[str, Any]:
    journal["status"] = status
    journal["reason"] = reason
    staging = (
        plan["_private"]["root"]
        / ".divan"
        / "adoption"
        / ".staging"
        / plan["proof_id"]
    )
    _atomic_journal(staging / "journal.json", journal)
    return {
        "schema_version": 1,
        "status": status,
        "proof_id": plan["proof_id"],
        "reason": reason,
        "receipt_status": "invalid",
        "files": [f".divan/adoption/.staging/{plan['proof_id']}/journal.json"],
    }


def execute_proof(
    plan: dict[str, Any],
    *,
    command_runner: Callable[..., execution.ExecutionResult] = execution.run,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    """Execute one proof plan once and promote only offline-verified evidence."""
    private = plan.get("_private")
    if not isinstance(private, dict):
        raise ValueError("proof plan has no private execution context")
    root = private.get("root")
    runner_path = private.get("runner_path")
    host = private.get("host")
    if (
        not isinstance(root, pathlib.Path)
        or not isinstance(runner_path, pathlib.Path)
        or not isinstance(host, str)
    ):
        raise ValueError("proof plan private execution context is invalid")
    final = root / ".divan" / "adoption" / str(plan.get("proof_id", ""))
    staging = (
        root
        / ".divan"
        / "adoption"
        / ".staging"
        / str(plan.get("proof_id", ""))
    )
    if final.exists():
        raise ValueError("final proof already exists and will not be overwritten")
    if staging.exists():
        raise ValueError("proof staging directory already exists")
    fresh = build_proof_plan(
        root,
        plan["goal"]["id"],
        host,
        plan["operator"]["role"],
        runner_path=runner_path,
    )
    if fresh["plan_digest"] != plan.get("plan_digest"):
        raise ValueError("proof inputs changed after preview")
    staging.mkdir(parents=True)
    started_at = _utc_text(clock())
    journal: dict[str, Any] = {
        "schema_version": 1,
        "proof_id": plan["proof_id"],
        "status": "running",
        "host_probe": {
            "status": "pending",
            "argv_sha256": _domain_hash(
                "divan-host-probe-v1", list(QUALIFYING_HOSTS[host])
            ),
        },
        "checks": [],
    }
    _atomic_journal(staging / "journal.json", journal)
    host_decision = timeouts.resolve_default("fast-check")
    host_result = command_runner(
        QUALIFYING_HOSTS[host],
        host_decision,
        mutating=False,
        cwd=str(root),
    )
    try:
        observed_version = _host_version(host_result)
    except ValueError as error:
        journal["host_probe"] = {
            **journal["host_probe"],
            "status": _result_status(host_result),
            "output_sha256": _domain_hash(
                "divan-host-probe-output-v1",
                {"stdout": host_result.stdout, "stderr": host_result.stderr},
            ),
        }
        return _failure_result(plan, journal, "blocked", str(error))
    journal["host_probe"] = {
        **journal["host_probe"],
        "status": "passed",
        "version": observed_version,
        "output_sha256": _domain_hash(
            "divan-host-probe-output-v1",
            {"stdout": host_result.stdout, "stderr": host_result.stderr},
        ),
    }
    _atomic_journal(staging / "journal.json", journal)
    baseline = _source_fingerprint(plan)
    receipt_checks: list[dict[str, Any]] = []
    for row in private["checks"]:
        pending = {
            "id": row["id"],
            "class": row["class"],
            "workspace_sha256": row["workspace_sha256"],
            "runner": row["runner"],
            "name": row["name"],
            "argv_sha256": row["argv_sha256"],
            "status": "pending",
            "timeout_ms": row["timeout_ms"],
            "timeout_policy_sha256": row["timeout_policy_sha256"],
        }
        journal["checks"].append(pending)
        _atomic_journal(staging / "journal.json", journal)
        decision = timeouts.resolve_default(row["timeout_class"])
        result = command_runner(
            row["argv"],
            decision,
            mutating=True,
            cwd=str(row["workspace_path"]),
        )
        public_result = _public_check_result(row, result)
        journal["checks"][-1] = public_result
        _atomic_journal(staging / "journal.json", journal)
        if public_result["status"] != "passed":
            status = (
                "cancelled"
                if public_result["status"] == "cancelled"
                else "failed-checks"
            )
            return _failure_result(
                plan,
                journal,
                status,
                f"check {row['id']} {public_result['status']}",
            )
        receipt_checks.append(public_result)
    if _source_fingerprint(plan) != baseline:
        return _failure_result(
            plan,
            journal,
            "invalid",
            "bounded project identity changed during proof",
        )
    completed_at = _utc_text(clock())
    receipt_value = adoption.build_clean_room_receipt(
        divan=plan["divan"],
        host={
            "name": host,
            "version": observed_version,
            "version_source": "observed-cli",
        },
        environment=plan["environment"],
        operator=plan["operator"],
        project=plan["project"],
        goal=plan["goal"],
        checks=receipt_checks,
        proof={
            "id": plan["proof_id"],
            "started_at": started_at,
            "completed_at": completed_at,
            "source_stable": True,
        },
    )
    json_path = staging / "adoption-receipt.json"
    markdown_path = staging / "adoption-receipt.md"
    json_path.write_bytes(adoption.serialize_adoption_json(receipt_value))
    markdown_path.write_bytes(
        adoption.serialize_adoption_markdown(receipt_value)
    )
    for path in (json_path, markdown_path):
        verification = adoption.verify_adoption(path)
        if (
            verification.get("status") != "valid-clean-room-adoption"
            or verification.get("eligible_for_v1") is not True
        ):
            return _failure_result(
                plan,
                journal,
                "invalid",
                "staged adoption receipt did not verify",
            )
    journal["status"] = "passed"
    receipt_proof = cast(dict[str, Any], receipt_value["proof"])
    journal["receipt_digest"] = receipt_proof["receipt_digest"]
    _atomic_journal(staging / "journal.json", journal)
    staging.rename(final)
    return {
        "schema_version": 1,
        "status": "passed",
        "proof_id": plan["proof_id"],
        "receipt_status": "valid-clean-room-adoption",
        "checks_passed": len(receipt_checks),
        "files": [
            f".divan/adoption/{plan['proof_id']}/adoption-receipt.json",
            f".divan/adoption/{plan['proof_id']}/adoption-receipt.md",
            f".divan/adoption/{plan['proof_id']}/journal.json",
        ],
    }
