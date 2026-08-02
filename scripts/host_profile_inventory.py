"""Inventory helpers shared by host installation profiles."""

from __future__ import annotations

import pathlib

import bootstrap_contract


def contained(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def expected_skill_names(root: pathlib.Path) -> set[str]:
    try:
        bundled = bootstrap_contract.load(root)
    except bootstrap_contract.ContractError as error:
        raise ValueError(str(error)) from error
    if bundled is not None:
        return {skill for row in bundled[1].values() for skill in row["skills"]}
    return {path.parent.name for path in root.glob("plugins/*/skills/*/SKILL.md")}


def expected_package_count(root: pathlib.Path) -> int:
    try:
        bundled = bootstrap_contract.load(root)
    except bootstrap_contract.ContractError as error:
        raise ValueError(str(error)) from error
    if bundled is not None:
        return len(bundled[1])
    return sum(1 for path in root.glob("plugins/*") if (path / "skills").is_dir())
