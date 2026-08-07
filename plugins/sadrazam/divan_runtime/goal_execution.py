"""Prepare a deterministic Divan goal for governed execution."""
from __future__ import annotations

import pathlib
from typing import Any

from . import receipts, seyir_state

PREPARABLE = {
    "DISCOVERED": ("SPECIFIED", "PLANNED"),
    "SPECIFIED": ("PLANNED",),
    "PLANNED": (),
}


def _root(project: pathlib.Path | str) -> pathlib.Path:
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    return root


def _receipt_path(root: pathlib.Path, goal_id: str) -> pathlib.Path:
    if receipts.GOAL_ID_PATTERN.fullmatch(goal_id) is None:
        raise ValueError("goal identifier is invalid")
    return root / ".divan" / "evidence" / goal_id / "receipt.json"


def prepare_goal(
    project: pathlib.Path | str,
    goal_id: str,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Validate goal artifacts and advance only to the PLANNED execution gate.

    This never skips a lifecycle phase. Receipt verification proves that the
    bound spec/plan/task artifacts still match their hashes before any state
    change is appended. The active Seyir cursor is rebound to the newest
    receipt event after execution.
    """
    root = _root(project)
    receipt_path = _receipt_path(root, goal_id)
    verification = receipts.verify_receipt(receipt_path)
    if not verification.get("ok"):
        errors = verification.get("errors") or ["goal receipt is invalid"]
        raise ValueError("; ".join(str(error) for error in errors))

    active = seyir_state.load(root)
    if active.get("active_goal_id") != goal_id:
        raise ValueError("goal preparation is limited to the active Divan goal")

    current = str(verification.get("state") or "")
    if current not in PREPARABLE:
        raise ValueError(
            f"goal state {current or 'UNKNOWN'} cannot be prepared for execution"
        )
    transitions = list(PREPARABLE[current])
    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "goal-execution-preparation",
        "status": "planned" if transitions else "ready",
        "goal_id": goal_id,
        "from": current,
        "to": "PLANNED",
        "transitions": transitions,
        "receipt": f".divan/evidence/{goal_id}/receipt.json",
    }
    if not execute:
        return result

    for destination in transitions:
        seyir_state.advance_goal(
            root,
            goal_id,
            destination,
            True,
            reason=(
                "Divan verified the bound goal artifacts and advanced the "
                "execution preparation gate."
            ),
        )

    rebound = seyir_state.load(root)
    seyir_state.update(
        root,
        goal_id,
        completed_task_ids=list(rebound["completed_task_ids"]),
        current_task_id=rebound["current_task_id"],
        next_task_id=rebound["next_task_id"],
        execute=True,
    )
    final = receipts.verify_receipt(receipt_path)
    if not final.get("ok") or final.get("state") != "PLANNED":
        raise ValueError("goal preparation did not produce a valid PLANNED receipt")
    result["status"] = "prepared" if transitions else "ready"
    result["from"] = current
    result["to"] = "PLANNED"
    return result
