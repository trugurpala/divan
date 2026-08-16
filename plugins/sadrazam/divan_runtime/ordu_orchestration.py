from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Mapping

from . import ordu
from .evidence import build_evidence
from .task_model import DivanTask

EvidenceAppender = Callable[[object], object]


def plan_ordu(task: DivanTask, append_evidence: EvidenceAppender) -> DivanTask:
    """Attach a deterministic Ordu plan and append its unit records in order."""
    work_plan = ordu.plan(task.title)
    metadata = dict(task.metadata)
    metadata["ordu"] = {
        "plan": work_plan,
        "unit_statuses": ordu.initial_unit_statuses(work_plan),
    }
    planned = replace(task, metadata=metadata)
    for unit in work_plan["units"]:
        assert isinstance(unit, Mapping)
        unit_id = str(unit["id"])
        append_evidence(
            build_evidence(
                planned.task_id,
                "ordu-unit",
                metadata["ordu"]["unit_statuses"][unit_id],
                f"Ordu unit {unit_id} planned",
                {
                    "unit_id": unit_id,
                    "role": str(unit["role"]),
                    "depends_on": list(unit["depends_on"]),
                    "phase": "planning",
                    "mutated": False,
                },
            )
        )
    return planned


def set_unit_status(task: DivanTask, unit_id: str, status: str) -> DivanTask:
    """Return task state with one planned Ordu unit status updated."""
    metadata = dict(task.metadata)
    ordu_data = metadata.get("ordu")
    if not isinstance(ordu_data, Mapping):
        return task
    statuses = ordu_data.get("unit_statuses")
    if not isinstance(statuses, Mapping) or unit_id not in statuses:
        return task
    next_ordu = dict(ordu_data)
    next_statuses = dict(statuses)
    next_statuses[unit_id] = status
    next_ordu["unit_statuses"] = next_statuses
    metadata["ordu"] = next_ordu
    return replace(task, metadata=metadata)


def record_unit(
    task: DivanTask,
    unit_id: str,
    status: str,
    *,
    phase: str,
    data: Mapping[str, Any],
    append_evidence: EvidenceAppender,
) -> None:
    """Append one unit evidence record without changing task metadata."""
    ordu_data = task.metadata.get("ordu")
    if not isinstance(ordu_data, Mapping):
        return
    plan_value = ordu_data.get("plan")
    if not isinstance(plan_value, Mapping):
        return
    units = plan_value.get("units")
    if not isinstance(units, list):
        return
    unit = next(
        (
            item
            for item in units
            if isinstance(item, Mapping) and item.get("id") == unit_id
        ),
        None,
    )
    if unit is None:
        return
    append_evidence(
        build_evidence(
            task.task_id,
            "ordu-unit",
            status,
            f"Ordu unit {unit_id} {status}",
            {
                "unit_id": unit_id,
                "role": str(unit["role"]),
                "depends_on": list(unit["depends_on"]),
                "phase": phase,
                **dict(data),
            },
        )
    )
