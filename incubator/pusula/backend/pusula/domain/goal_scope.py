from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import ceil
from typing import Iterable


class ScopeCategory(StrEnum):
    ACCEPTANCE = "acceptance"
    RISK = "risk"
    CHANGE = "change"


@dataclass(frozen=True, slots=True)
class ScopeUnit:
    unit_id: str
    category: ScopeCategory
    description: str

    def validate(self) -> None:
        if not self.unit_id.strip():
            raise ValueError("unit_id is required")
        if not self.description.strip():
            raise ValueError("description is required")


@dataclass(frozen=True, slots=True)
class ScopeSlice:
    slice_id: str
    units: tuple[ScopeUnit, ...]

    def validate(self, total_units: int) -> None:
        if not self.slice_id.strip():
            raise ValueError("slice_id is required")
        if not self.units:
            raise ValueError("scope slice cannot be empty")
        if len(self.units) * 4 > total_units:
            raise ValueError("scope slice exceeds the 25 percent budget")


@dataclass(frozen=True, slots=True)
class GoalRecord:
    goal_id: str
    team_id: str

    def validate(self) -> None:
        if not self.goal_id.strip():
            raise ValueError("goal_id is required")
        if not self.team_id.strip():
            raise ValueError("team_id is required")


@dataclass(frozen=True, slots=True)
class GoalRevision:
    goal_id: str
    revision: int
    statement: str
    scope_units: tuple[ScopeUnit, ...]
    supersedes_revision: int | None

    def validate(self) -> None:
        if not self.goal_id.strip():
            raise ValueError("goal_id is required")
        if self.revision < 1:
            raise ValueError("revision must be positive")
        if not self.statement.strip():
            raise ValueError("statement is required")
        if self.revision == 1 and self.supersedes_revision is not None:
            raise ValueError("first revision cannot supersede another revision")
        if self.revision > 1 and self.supersedes_revision != self.revision - 1:
            raise ValueError("revision must supersede the immediately previous revision")
        _validate_scope_units(self.scope_units)


def _validate_scope_units(units: tuple[ScopeUnit, ...]) -> None:
    if len(units) < 4:
        raise ValueError("automatic execution requires at least four objective scope units")
    ids: set[str] = set()
    for unit in units:
        unit.validate()
        if unit.unit_id in ids:
            raise ValueError("scope unit ids must be unique")
        ids.add(unit.unit_id)


def build_revision(
    *,
    goal_id: str,
    statement: str,
    scope_units: Iterable[ScopeUnit],
    previous: GoalRevision | None = None,
) -> GoalRevision:
    units = tuple(scope_units)
    revision = 1 if previous is None else previous.revision + 1
    if previous is not None and previous.goal_id != goal_id:
        raise ValueError("previous revision belongs to a different goal")
    result = GoalRevision(
        goal_id=goal_id,
        revision=revision,
        statement=statement,
        scope_units=units,
        supersedes_revision=None if previous is None else previous.revision,
    )
    result.validate()
    return result


def build_scope_slices(units: Iterable[ScopeUnit]) -> tuple[ScopeSlice, ...]:
    rows = tuple(units)
    _validate_scope_units(rows)
    ordered = tuple(sorted(rows, key=lambda unit: (unit.category.value, unit.unit_id)))
    max_units_per_slice = max(1, len(ordered) // 4)
    slice_count = ceil(len(ordered) / max_units_per_slice)
    slices: list[ScopeSlice] = []
    for index in range(slice_count):
        start = len(ordered) * index // slice_count
        end = len(ordered) * (index + 1) // slice_count
        scope_slice = ScopeSlice(
            slice_id=f"slice-{index + 1:03d}",
            units=ordered[start:end],
        )
        scope_slice.validate(len(ordered))
        slices.append(scope_slice)
    return tuple(slices)
