"""Governed Orca execution bound to Divan goal receipts.

This module is the product boundary between Divan-owned planning/evidence and
an optional Orca execution sidecar.  It deliberately does not own planning,
review verdicts, or release decisions.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from . import governance, receipts
from .orca_engine import ExecutionAuthority, OrcaEngine, OrcaResult

GOAL_ID_PATTERN = re.compile(r"^goal-[0-9a-f]{12}$")
EXECUTABLE_STATES = frozenset({"PLANNED", "IMPLEMENTING"})
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
        "worktree_name": worktree_name,
        "agent": agent or "default",
        "repo_selector": repo_selector or "active",
    }
    return governance.authorize_mutation(
        actor_id,
        "engine.orca.worktree.create",
        scope,
        explicit_authority=execute,
        directory=RUNTIME_DIRECTORY,
    )


def _evidence(result: OrcaResult, mandate_id: str, name: str, agent: str | None) -> list[str]:
    rows = [
        "engine:orca",
        f"action:{result.action}",
        f"worktree:{receipts.redact_text(name)}",
        f"mandate:{mandate_id}",
        f"exit-code:{result.exit_code}",
    ]
    if agent:
        rows.append(f"agent:{receipts.redact_text(agent)}")
    return rows


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
    """Create one Orca worktree under an explicit Divan mandate.

    The goal must already be PLANNED or IMPLEMENTING.  A successful first
    execution advances PLANNED -> IMPLEMENTING and records only redacted,
    non-prompt execution evidence in the goal receipt.
    """
    root = _project_root(project)
    identifier = _goal_id(goal_id)
    receipt_path, receipt = _receipt(root, identifier)
    state = str(receipt.get("state", ""))
    if state not in EXECUTABLE_STATES:
        allowed = ", ".join(sorted(EXECUTABLE_STATES))
        raise ValueError(f"goal state {state or 'UNKNOWN'} cannot execute Orca; expected {allowed}")

    mandate = _authority(
        goal_id=identifier,
        worktree_name=name,
        agent=agent,
        repo_selector=repo_selector,
        actor_id=actor_id,
        execute=execute,
    )
    authority = ExecutionAuthority(execute=True, mandate_id=str(mandate["mandate_id"]))
    runtime = engine or OrcaEngine()
    result = runtime.worktree_create(
        name=name,
        authority=authority,
        repo_selector=repo_selector,
        agent=agent,
        prompt=prompt,
        setup=setup,
    )
    if not result.ok:
        return {
            "schema_version": 1,
            "kind": "engine-execution",
            "status": "failed",
            "goal_id": identifier,
            "goal_state": state,
            "authority": mandate,
            "engine_result": result.to_dict(),
            "receipt_updated": False,
        }

    receipt_updated = False
    next_state = state
    if state == "PLANNED":
        updated = receipts.append_transition(
            receipt_path,
            "IMPLEMENTING",
            reason="Orca worktree execution started under an explicit Divan mandate.",
            evidence=_evidence(result, str(mandate["mandate_id"]), name, agent),
        )
        next_state = str(updated["state"])
        receipt_updated = True

    return {
        "schema_version": 1,
        "kind": "engine-execution",
        "status": "started",
        "goal_id": identifier,
        "goal_state": next_state,
        "authority": mandate,
        "engine_result": result.to_dict(),
        "receipt_updated": receipt_updated,
    }


def status(engine: OrcaEngine | None = None) -> dict[str, Any]:
    """Return a read-only, stable Orca engine health snapshot."""
    result = (engine or OrcaEngine()).status()
    return {
        "schema_version": 1,
        "kind": "engine-status",
        "engine": "orca",
        "status": "ready" if result.ok else "unavailable",
        "engine_result": result.to_dict(),
    }
