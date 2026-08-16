"""Deterministic task graph planning for Ottoman's local Ordu layer."""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

MAX_PARALLEL_WORKERS = 4
PLANNING_UNIT_IDS = frozenset({"discover", "plan", "quality-map"})


@dataclass(frozen=True)
class OrduUnit:
    id: str
    role: str
    title: str
    depends_on: tuple[str, ...] = ()


def worker_budget(logical_cpus: int | None = None) -> int:
    """Reserve four cores for the desktop/OS and bound autonomous work."""
    available = logical_cpus if logical_cpus is not None else os.cpu_count()
    return min(MAX_PARALLEL_WORKERS, max(1, (available or 4) - 4))


def plan(title: str, *, logical_cpus: int | None = None) -> dict[str, Any]:
    task = title.strip()
    if not task:
        raise ValueError("Ordu task title is required")
    if len(task) > 500:
        raise ValueError("Ordu task title is too long")
    units = (
        OrduUnit("discover", "discovery", "Kapsam ve etkiyi çıkar"),
        OrduUnit("plan", "planning", "Uygulama planını ve kabul kriterlerini yaz", ("discover",)),
        OrduUnit(
            "quality-map",
            "quality",
            "Test, güvenlik ve geri dönüş kapılarını eşleştir",
            ("plan",),
        ),
        OrduUnit("implement", "implementation", task, ("plan",)),
        OrduUnit(
            "verify",
            "verification",
            "Test, build ve güvenlik kapılarını çalıştır",
            ("implement", "quality-map"),
        ),
        OrduUnit("review", "review", "Diff ve kanıtı bağımsız incele", ("verify",)),
    )
    _validate(units)
    return {
        "title": task,
        "max_parallel_workers": worker_budget(logical_cpus),
        "units": [asdict(unit) for unit in units],
        "execution": "planned-only",
        "approval_required_before_mutation": True,
    }


def initial_unit_statuses(plan_value: dict[str, Any]) -> dict[str, str]:
    """Return the truthful first receipt state for every generated Ordu unit.

    Creating the deterministic plan completes the non-mutating planning units;
    implementation, verification and independent review remain pending until
    their own workflow gates produce evidence.
    """
    units = plan_value.get("units")
    if not isinstance(units, list):
        raise ValueError("Ordu plan units must be a list")
    statuses: dict[str, str] = {}
    for unit in units:
        if not isinstance(unit, dict) or not isinstance(unit.get("id"), str):
            raise ValueError("Ordu plan unit is invalid")
        unit_id = unit["id"]
        statuses[unit_id] = "pass" if unit_id in PLANNING_UNIT_IDS else "pending"
    return statuses


def _validate(units: tuple[OrduUnit, ...]) -> None:
    ids = {unit.id for unit in units}
    if len(ids) != len(units):
        raise ValueError("Ordu unit identifiers must be unique")
    for unit in units:
        if any(dependency not in ids for dependency in unit.depends_on):
            raise ValueError("Ordu dependency is unknown")
    visiting: set[str] = set()
    visited: set[str] = set()
    by_id = {unit.id: unit for unit in units}

    def visit(unit_id: str) -> None:
        if unit_id in visiting:
            raise ValueError("Ordu graph cannot contain a cycle")
        if unit_id in visited:
            return
        visiting.add(unit_id)
        for dependency in by_id[unit_id].depends_on:
            visit(dependency)
        visiting.remove(unit_id)
        visited.add(unit_id)

    for unit in units:
        visit(unit.id)
