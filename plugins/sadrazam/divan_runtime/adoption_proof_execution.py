"""One-shot execution and sealing for a precomputed clean-room proof plan."""
from __future__ import annotations

import os
import pathlib
import shutil
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

from . import (
    adoption,
    execution,
    project_state,
    receipts,
    timeouts,
)
from . import (
    adoption_proof_common as common,
)


def _atomic_journal(path: pathlib.Path, value: dict[str, Any]) -> None:
    receipts._atomic_json(path, value)


def _proof_paths(plan: dict[str, Any]) -> tuple[pathlib.Path, pathlib.Path]:
    root = plan["_private"]["root"]
    proof_id = str(plan.get("proof_id", ""))
    base = root / ".divan" / "adoption"
    return base / proof_id, base / ".staging" / proof_id


def _source_fingerprint(plan: dict[str, Any]) -> str:
    private = plan["_private"]
    root = private["root"]
    workspaces = sorted(
        {row["workspace_path"] for row in private["checks"]},
        key=lambda item: item.as_posix(),
    )
    markers = (
        "package.json", "pyproject.toml", "requirements.txt",
        "setup.py", "go.mod", "Cargo.toml",
    )
    files: set[pathlib.Path] = {
        root / ".divan" / "config.json",
        root / ".divan" / "install-state.json",
        private["receipt_path"],
    }
    for workspace in workspaces:
        files.update(
            candidate
            for marker in markers
            if (candidate := workspace / marker).exists()
        )
    rows = [_fingerprint_row(root, path) for path in sorted(files)]
    return common.domain_hash("divan-proof-source-fingerprint-v1", rows)


def _fingerprint_row(root: pathlib.Path, path: pathlib.Path) -> dict[str, str]:
    if project_state._is_reparse_or_symlink(path):
        raise ValueError("proof identity input uses a symlink or reparse point")
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError("proof identity input escapes the project") from error
    if not resolved.is_file() or resolved.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("proof identity input is unavailable or too large")
    return {
        "path_sha256": common.domain_hash(
            "divan-proof-identity-path-v1", relative
        ),
        "content_sha256": common.hash_bytes(resolved.read_bytes()),
    }


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
    duration_ms = min(
        max(0, round(result.elapsed_seconds * 1000)), row["timeout_ms"]
    )
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
        "output_sha256": common.domain_hash(
            "divan-proof-output-v1",
            {"stdout": result.stdout, "stderr": result.stderr},
        ),
    }


def _failure_result(
    plan: dict[str, Any], journal: dict[str, Any], status: str, reason: str
) -> dict[str, Any]:
    journal.update({"status": status, "reason": reason})
    _final, staging = _proof_paths(plan)
    _atomic_journal(staging / "journal.json", journal)
    return {
        "schema_version": 1,
        "status": status,
        "proof_id": plan["proof_id"],
        "reason": reason,
        "receipt_status": "invalid",
        "files": [f".divan/adoption/.staging/{plan['proof_id']}/journal.json"],
    }


def _execution_context(
    plan: dict[str, Any],
    plan_builder: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], pathlib.Path, pathlib.Path, str]:
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
    final, staging = _proof_paths(plan)
    if final.exists():
        raise ValueError("final proof already exists and will not be overwritten")
    if staging.exists():
        raise ValueError("proof staging directory already exists")
    fresh = plan_builder(
        root,
        plan["goal"]["id"],
        host,
        plan["operator"]["role"],
        runner_path=runner_path,
        expected_runner_sha256=plan["divan"]["runner_sha256"],
    )
    if fresh["plan_digest"] != plan.get("plan_digest"):
        raise ValueError("proof inputs changed after preview")
    return fresh, final, staging, host


def _initial_journal(plan: dict[str, Any], host: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "proof_id": plan["proof_id"],
        "status": "running",
        "host_probe": {
            "status": "pending",
            "argv_sha256": common.domain_hash(
                "divan-host-probe-v1", list(common.QUALIFYING_HOSTS[host])
            ),
        },
        "checks": [],
    }


def _resolved_host_probe_command(
    host: str,
    *,
    platform: str = os.name,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[str, ...]:
    command = common.QUALIFYING_HOSTS[host]
    if platform != "nt":
        return command
    executable, *arguments = command
    for suffix in (".cmd", ".exe"):
        if resolved := which(executable + suffix):
            return (resolved, *arguments)
    return command


def _run_host_probe(
    plan: dict[str, Any],
    journal: dict[str, Any],
    host: str,
    runner: Callable[..., execution.ExecutionResult],
) -> str | dict[str, Any]:
    root = plan["_private"]["root"]
    result = runner(
        _resolved_host_probe_command(host),
        timeouts.resolve_default("fast-check"),
        mutating=False,
        cwd=str(root),
    )
    output_hash = common.domain_hash(
        "divan-host-probe-output-v1",
        {"stdout": result.stdout, "stderr": result.stderr},
    )
    try:
        version = _host_version(result)
    except ValueError as error:
        journal["host_probe"].update(
            {"status": _result_status(result), "output_sha256": output_hash}
        )
        return _failure_result(plan, journal, "blocked", str(error))
    journal["host_probe"].update(
        {"status": "passed", "version": version, "output_sha256": output_hash}
    )
    _final, staging = _proof_paths(plan)
    _atomic_journal(staging / "journal.json", journal)
    return version


def _pending_check(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "id", "class", "workspace_sha256", "runner", "name",
            "argv_sha256", "timeout_ms", "timeout_policy_sha256",
        )
    } | {"status": "pending"}


def _run_checks(
    plan: dict[str, Any],
    journal: dict[str, Any],
    runner: Callable[..., execution.ExecutionResult],
) -> list[dict[str, Any]] | dict[str, Any]:
    _final, staging = _proof_paths(plan)
    passed: list[dict[str, Any]] = []
    for row in plan["_private"]["checks"]:
        journal["checks"].append(_pending_check(row))
        _atomic_journal(staging / "journal.json", journal)
        result = runner(
            row["argv"],
            timeouts.resolve_default(row["timeout_class"]),
            mutating=True,
            cwd=str(row["workspace_path"]),
        )
        public = _public_check_result(row, result)
        journal["checks"][-1] = public
        _atomic_journal(staging / "journal.json", journal)
        if public["status"] != "passed":
            status = "cancelled" if public["status"] == "cancelled" else "failed-checks"
            return _failure_result(
                plan, journal, status, f"check {row['id']} {public['status']}"
            )
        passed.append(public)
    return passed


def _tracked_source_digest(
    plan: dict[str, Any],
    runner: Callable[..., execution.ExecutionResult],
) -> str:
    root = plan["_private"]["root"]
    commands = (
        ("git", "rev-parse", "--verify", "HEAD"),
        ("git", "diff", "--binary", "HEAD", "--"),
        ("git", "diff", "--cached", "--binary", "HEAD", "--"),
    )
    rows: list[dict[str, str]] = []
    for command in commands:
        result = runner(
            command,
            timeouts.resolve_default("fast-check"),
            mutating=False,
            cwd=str(root),
        )
        if result.status != "PASS" or result.returncode != 0:
            raise ValueError("Git tracked source probe did not pass")
        rows.append(
            {
                "argv_sha256": common.domain_hash(
                    "divan-git-source-argv-v1", list(command)
                ),
                "output_sha256": common.domain_hash(
                    "divan-git-source-output-v1",
                    {"stdout": result.stdout, "stderr": result.stderr},
                ),
            }
        )
    return common.domain_hash("divan-git-tracked-source-v1", rows)


def _seal_receipt(
    plan: dict[str, Any],
    journal: dict[str, Any],
    host: str,
    version: str,
    checks: list[dict[str, Any]],
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    final, staging = _proof_paths(plan)
    receipt = adoption.build_clean_room_receipt(
        divan=plan["divan"],
        host={"name": host, "version": version, "version_source": "observed-cli"},
        environment=plan["environment"],
        operator=plan["operator"],
        project=plan["project"],
        goal=plan["goal"],
        checks=checks,
        proof={
            "id": plan["proof_id"],
            "started_at": started_at,
            "completed_at": completed_at,
            "source_stable": True,
        },
    )
    paths = (staging / "adoption-receipt.json", staging / "adoption-receipt.md")
    paths[0].write_bytes(adoption.serialize_adoption_json(receipt))
    paths[1].write_bytes(adoption.serialize_adoption_markdown(receipt))
    if any(
        adoption.verify_adoption(path).get("status") != "valid-clean-room-adoption"
        or adoption.verify_adoption(path).get("eligible_for_v1") is not True
        for path in paths
    ):
        return _failure_result(
            plan, journal, "invalid", "staged adoption receipt did not verify"
        )
    journal["status"] = "passed"
    receipt_proof = cast(dict[str, Any], receipt["proof"])
    journal["receipt_digest"] = receipt_proof["receipt_digest"]
    _atomic_journal(staging / "journal.json", journal)
    staging.rename(final)
    return {
        "schema_version": 1,
        "status": "passed",
        "proof_id": plan["proof_id"],
        "receipt_status": "valid-clean-room-adoption",
        "checks_passed": len(checks),
        "files": [
            f".divan/adoption/{plan['proof_id']}/adoption-receipt.json",
            f".divan/adoption/{plan['proof_id']}/adoption-receipt.md",
            f".divan/adoption/{plan['proof_id']}/journal.json",
        ],
    }


def execute_proof(
    plan: dict[str, Any],
    *,
    plan_builder: Callable[..., dict[str, Any]],
    command_runner: Callable[..., execution.ExecutionResult] = execution.run,
    clock: Callable[[], datetime] = common.utc_now,
) -> dict[str, Any]:
    """Execute one proof plan once and promote only offline-verified evidence."""
    active_plan, _final, staging, host = _execution_context(plan, plan_builder)
    staging.mkdir(parents=True)
    started_at = common.utc_text(clock())
    journal = _initial_journal(active_plan, host)
    _atomic_journal(staging / "journal.json", journal)
    observed = _run_host_probe(active_plan, journal, host, command_runner)
    if isinstance(observed, dict):
        return observed
    baseline = _source_fingerprint(active_plan)
    try:
        tracked_baseline = _tracked_source_digest(active_plan, command_runner)
    except ValueError as error:
        return _failure_result(active_plan, journal, "blocked", str(error))
    check_results = _run_checks(active_plan, journal, command_runner)
    if isinstance(check_results, dict):
        return check_results
    if _source_fingerprint(active_plan) != baseline:
        return _failure_result(
            active_plan, journal, "invalid",
            "bounded project identity changed during proof",
        )
    try:
        tracked_changed = (
            _tracked_source_digest(active_plan, command_runner)
            != tracked_baseline
        )
    except ValueError as error:
        return _failure_result(active_plan, journal, "blocked", str(error))
    if tracked_changed:
        return _failure_result(
            active_plan, journal, "invalid",
            "Git tracked source changed during proof",
        )
    return _seal_receipt(
        active_plan, journal, host, observed, check_results,
        started_at, common.utc_text(clock())
    )
