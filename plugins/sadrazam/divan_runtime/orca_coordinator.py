"""Governed Orca execution bound to Divan goal receipts.

This module is the product boundary between Divan-owned planning/evidence and
an optional Orca execution sidecar. It deliberately does not own planning,
review verdicts, or release decisions.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
from typing import Any

from . import governance, receipts
from .orca_engine import ExecutionAuthority, OrcaEngine, OrcaResult

GOAL_ID_PATTERN = re.compile(r"^goal-[0-9a-f]{12}$")
EXECUTABLE_STATES = frozenset({"PLANNED"})
RUNTIME_DIRECTORY = pathlib.Path(__file__).resolve().parent


def _project_root(project: pathlib.Path | str) -> pathlib.Path:
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    return root


def _goal_id(value: str) -> str:
    if not isinstance(value, str) or GOAL_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("goal identifier must match goal-[0-9a-f]{12}")
    return value


def _receipt_path(root: pathlib.Path, goal_id: str) -> pathlib.Path:
    return root / ".divan" / "evidence" / _goal_id(goal_id) / "receipt.json"


def _receipt(root: pathlib.Path, goal_id: str) -> tuple[pathlib.Path, dict[str, Any]]:
    path = _receipt_path(root, goal_id)
    verification = receipts.verify_receipt(path)
    if not verification.get("ok"):
        errors = verification.get("errors") or ["goal receipt is invalid"]
        raise ValueError("; ".join(str(error) for error in errors))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("goal receipt cannot be read") from error
    if not isinstance(value, dict):
        raise ValueError("goal receipt root must be an object")
    return path, value


def _authority(
    *,
    goal_id: str,
    worktree_name: str,
    agent: str | None,
    repo_selector: str | None,
    actor_id: str,
    execute: bool,
) -> dict[str, Any]:
    scope = {
        "engine": "orca",
        "goal_id": goal_id,
        "worktree_name": receipts.redact_text(worktree_name),
        "agent": receipts.redact_text(agent) if agent else "default",
        "repo_selector": (
            receipts.redact_text(repo_selector) if repo_selector else "active"
        ),
    }
    return governance.authorize_mutation(
        actor_id,
        "engine.orca.worktree.create",
        scope,
        explicit_authority=execute,
        directory=RUNTIME_DIRECTORY,
    )


def _redacted(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _redacted(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redacted(item) for item in value]
    if isinstance(value, tuple):
        return [_redacted(item) for item in value]
    if isinstance(value, str):
        return receipts.redact_text(value)
    return value


def _public_result(result: OrcaResult) -> dict[str, Any]:
    return _redacted(result.to_dict())


def _evidence_relative(goal_id: str, mandate_id: str, action: str) -> str:
    fingerprint = hashlib.sha256(
        f"{goal_id}:{mandate_id}:{action}".encode("utf-8")
    ).hexdigest()[:16]
    return f".divan/evidence/{goal_id}/engine/orca-{fingerprint}.json"


def _evidence_value(
    result: OrcaResult,
    *,
    goal_id: str,
    mandate_id: str,
    name: str,
    agent: str | None,
    repo_selector: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "engine": "orca",
        "action": result.action,
        "goal_id": goal_id,
        "mandate_id": mandate_id,
        "worktree_name": receipts.redact_text(name),
        "agent": receipts.redact_text(agent) if agent else None,
        "repo_selector": (
            receipts.redact_text(repo_selector) if repo_selector else "active"
        ),
        "exit_code": result.exit_code,
        "argv": [receipts.redact_text(item) for item in result.argv],
    }


def _atomic_evidence(path: pathlib.Path, value: dict[str, Any]) -> tuple[str, bool]:
    content = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    if path.exists():
        if not path.is_file() or path.read_bytes() != content:
            raise ValueError("Orca evidence path already exists with different content")
        return digest, False
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return digest, True


def _record_execution(
    root: pathlib.Path,
    receipt_path: pathlib.Path,
    result: OrcaResult,
    *,
    goal_id: str,
    mandate_id: str,
    name: str,
    agent: str | None,
    repo_selector: str | None,
) -> tuple[dict[str, Any] | None, str, str | None]:
    relative = _evidence_relative(goal_id, mandate_id, result.action)
    path = root.joinpath(*pathlib.PurePosixPath(relative).parts)
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ValueError("Orca evidence path escapes project") from error
    value = _evidence_value(
        result,
        goal_id=goal_id,
        mandate_id=mandate_id,
        name=name,
        agent=agent,
        repo_selector=repo_selector,
    )
    digest, _ = _atomic_evidence(path, value)
    content_errors = receipts._artifact_content_errors(path, "Orca execution evidence")
    if content_errors:
        raise ValueError("; ".join(content_errors))
    try:
        updated = receipts.append_transition(
            receipt_path,
            "IMPLEMENTING",
            reason="Orca worktree execution started under an explicit Divan mandate.",
            evidence=[relative],
            bind_artifacts={relative: digest},
        )
    except ValueError as error:
        return None, relative, str(error)
    return updated, relative, None


def create_worktree(
    project: pathlib.Path | str,
    goal_id: str,
    *,
    name: str,
    actor_id: str = "owner",
    execute: bool = False,
    repo_selector: str | None = None,
    agent: str | None = None,
    prompt: str | None = None,
    setup: str = "inherit",
    engine: OrcaEngine | None = None,
) -> dict[str, Any]:
    """Create the first Orca worktree for a PLANNED goal under a Divan mandate.

    A successful engine mutation is written as a redacted JSON artifact, bound
    to the receipt by SHA-256, then advances PLANNED -> IMPLEMENTING. If the
    evidence bind fails after Orca succeeds, automatic retry is forbidden so a
    duplicate worktree is not created accidentally.
    """
    root = _project_root(project)
    identifier = _goal_id(goal_id)
    receipt_path, receipt = _receipt(root, identifier)
    state = str(receipt.get("state", ""))
    if state not in EXECUTABLE_STATES:
        raise ValueError(
            f"goal state {state or 'UNKNOWN'} cannot execute Orca; expected PLANNED"
        )

    mandate = _authority(
        goal_id=identifier,
        worktree_name=name,
        agent=agent,
        repo_selector=repo_selector,
        actor_id=actor_id,
        execute=execute,
    )
    mandate_id = str(mandate["mandate_id"])
    authority = ExecutionAuthority(execute=True, mandate_id=mandate_id)
    runtime = engine or OrcaEngine()
    result = runtime.worktree_create(
        name=name,
        authority=authority,
        repo_selector=repo_selector,
        agent=agent,
        prompt=prompt,
        setup=setup,
    )
    public_result = _public_result(result)
    if not result.ok:
        return {
            "schema_version": 1,
            "kind": "engine-execution",
            "status": "failed",
            "goal_id": identifier,
            "goal_state": state,
            "authority": mandate,
            "engine_result": public_result,
            "receipt_updated": False,
            "retry_allowed": False,
        }

    updated, evidence_path, bind_error = _record_execution(
        root,
        receipt_path,
        result,
        goal_id=identifier,
        mandate_id=mandate_id,
        name=name,
        agent=agent,
        repo_selector=repo_selector,
    )
    if updated is None:
        return {
            "schema_version": 1,
            "kind": "engine-execution",
            "status": "evidence-pending",
            "goal_id": identifier,
            "goal_state": state,
            "authority": mandate,
            "engine_result": public_result,
            "evidence": evidence_path,
            "receipt_updated": False,
            "retry_allowed": False,
            "errors": [f"Orca succeeded but receipt binding failed: {bind_error}"],
        }

    return {
        "schema_version": 1,
        "kind": "engine-execution",
        "status": "started",
        "goal_id": identifier,
        "goal_state": str(updated["state"]),
        "authority": mandate,
        "engine_result": public_result,
        "evidence": evidence_path,
        "receipt_updated": True,
        "retry_allowed": False,
    }


def status(engine: OrcaEngine | None = None) -> dict[str, Any]:
    """Return a read-only, stable Orca engine health snapshot."""
    result = (engine or OrcaEngine()).status()
    return {
        "schema_version": 1,
        "kind": "engine-status",
        "engine": "orca",
        "status": "ready" if result.ok else "unavailable",
        "engine_result": _public_result(result),
    }
