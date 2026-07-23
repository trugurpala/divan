#!/usr/bin/env python3
"""Read-only project intelligence and impact routing for Divan Company OS."""
from __future__ import annotations

import fnmatch
import json
import pathlib
import re
from collections import deque
from typing import Any, NamedTuple

MAX_MARKER_BYTES = 1_000_000
CONTRACT_FILES = {
    "roles": "roles.json",
    "workflows": "workflows.json",
    "frameworks": "frameworks.json",
    "impact": "impact-graph.json",
}
PACKAGE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SkillRef(NamedTuple):
    package: str
    skill: str


class Role(NamedTuple):
    id: str
    label: dict[str, str]
    mission: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    skills: tuple[SkillRef, ...]
    gates: tuple[str, ...]


class Workflow(NamedTuple):
    id: str
    label: dict[str, str]
    priority: int
    keywords: tuple[str, ...]
    roles: tuple[str, ...]
    skills: tuple[SkillRef, ...]
    stages: tuple[str, ...]


class Framework(NamedTuple):
    id: str
    label: dict[str, str]
    fallback: bool
    detectors: tuple[dict[str, Any], ...]
    skills: tuple[SkillRef, ...]
    checks: tuple[str, ...]


class ImpactRule(NamedTuple):
    id: str
    patterns: tuple[str, ...]
    effects: tuple[str, ...]
    checks: tuple[str, ...]


class Contracts(NamedTuple):
    roles: dict[str, Role]
    workflows: dict[str, Workflow]
    frameworks: dict[str, Framework]
    impact_rules: tuple[ImpactRule, ...]
    effect_edges: dict[str, tuple[str, ...]]
    effect_checks: dict[str, tuple[str, ...]]


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid company contract: {path.name}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"invalid company contract schema: {path.name}")
    return value


def _identifier(value: Any, context: str) -> str:
    if not isinstance(value, str) or not PACKAGE_NAME.fullmatch(value):
        raise ValueError(f"{context} must be an English kebab-case identifier")
    return value


def _strings(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{context} must be a non-empty string list")
    return tuple(item.strip() for item in value)


def _label(value: Any, context: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"en", "tr"}:
        raise ValueError(f"{context} requires exact en/tr labels")
    if not all(isinstance(item, str) and item.strip() for item in value.values()):
        raise ValueError(f"{context} labels cannot be empty")
    return {"en": value["en"].strip(), "tr": value["tr"].strip()}


def _skills(value: Any, context: str) -> tuple[SkillRef, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{context} skills must be a list")
    skills: list[SkillRef] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"package", "skill"}:
            raise ValueError(f"{context} skill {index} is invalid")
        skills.append(
            SkillRef(
                _identifier(item["package"], f"{context} package"),
                _identifier(item["skill"], f"{context} skill"),
            )
        )
    return tuple(skills)


def _unique(rows: list[Any], context: str) -> None:
    identifiers = [row.id for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"duplicate {context} identifier")


def _load_roles(value: dict[str, Any]) -> dict[str, Role]:
    rows = value.get("roles")
    if not isinstance(rows, list):
        raise ValueError("roles must be a list")
    roles = [
        Role(
            _identifier(row.get("id"), "role id"),
            _label(row.get("label"), "role"),
            str(row.get("mission", "")).strip(),
            _strings(row.get("inputs"), "role inputs"),
            _strings(row.get("outputs"), "role outputs"),
            _skills(row.get("skills"), "role"),
            _strings(row.get("gates"), "role gates"),
        )
        for row in rows
        if isinstance(row, dict)
    ]
    if len(roles) != len(rows) or any(not role.mission for role in roles):
        raise ValueError("every role requires a mission")
    _unique(roles, "role")
    return {role.id: role for role in roles}


def _load_workflows(
    value: dict[str, Any], roles: dict[str, Role]
) -> dict[str, Workflow]:
    rows = value.get("workflows")
    if not isinstance(rows, list):
        raise ValueError("workflows must be a list")
    workflows: list[Workflow] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("priority"), int):
            raise ValueError("workflow row is invalid")
        role_ids = _strings(row.get("roles"), "workflow roles")
        unknown = sorted(set(role_ids) - set(roles))
        if unknown:
            raise ValueError(f"workflow references unknown role: {', '.join(unknown)}")
        workflows.append(
            Workflow(
                _identifier(row.get("id"), "workflow id"),
                _label(row.get("label"), "workflow"),
                row["priority"],
                _strings(row.get("keywords"), "workflow keywords"),
                role_ids,
                _skills(row.get("skills"), "workflow"),
                _strings(row.get("stages"), "workflow stages"),
            )
        )
    _unique(workflows, "workflow")
    return {workflow.id: workflow for workflow in workflows}


def _safe_relative(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} path is required")
    normalized = value.replace("\\", "/")
    pure = pathlib.PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"{context} path must be relative")
    return pure.as_posix()


def _load_frameworks(value: dict[str, Any]) -> dict[str, Framework]:
    rows = value.get("frameworks")
    if not isinstance(rows, list):
        raise ValueError("frameworks must be a list")
    frameworks: list[Framework] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("detectors"), list):
            raise ValueError("framework row is invalid")
        detectors: list[dict[str, Any]] = []
        for detector in row["detectors"]:
            if not isinstance(detector, dict) or detector.get("kind") not in {
                "path-exists",
                "package-json-dependency",
            }:
                raise ValueError("framework detector is invalid")
            normalized = dict(detector)
            normalized["path"] = _safe_relative(detector.get("path"), "detector")
            if detector["kind"] == "package-json-dependency":
                normalized["values"] = list(
                    _strings(detector.get("values"), "detector values")
                )
            detectors.append(normalized)
        frameworks.append(
            Framework(
                _identifier(row.get("id"), "framework id"),
                _label(row.get("label"), "framework"),
                row.get("fallback") is True,
                tuple(detectors),
                _skills(row.get("skills"), "framework"),
                _strings(row.get("checks"), "framework checks"),
            )
        )
    _unique(frameworks, "framework")
    if sum(framework.fallback for framework in frameworks) != 1:
        raise ValueError("exactly one fallback framework is required")
    return {framework.id: framework for framework in frameworks}


def _load_impact(
    value: dict[str, Any],
) -> tuple[
    tuple[ImpactRule, ...],
    dict[str, tuple[str, ...]],
    dict[str, tuple[str, ...]],
]:
    edge_rows, check_rows, rows = (
        value.get("effect_edges"),
        value.get("effect_checks"),
        value.get("rules"),
    )
    if not isinstance(edge_rows, dict) or not isinstance(check_rows, dict):
        raise ValueError("impact effect maps are invalid")
    if not isinstance(rows, list):
        raise ValueError("impact rules must be a list")
    edges = {
        _identifier(key, "effect"): _strings(items, f"{key} edges")
        for key, items in edge_rows.items()
    }
    checks = {
        _identifier(key, "effect"): _strings(items, f"{key} checks")
        for key, items in check_rows.items()
    }
    rules: list[ImpactRule] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("impact rule is invalid")
        patterns = _strings(row.get("patterns"), "impact patterns")
        for pattern in patterns:
            _safe_relative(pattern, "impact pattern")
        raw_checks = row.get("checks")
        if not isinstance(raw_checks, list) or not all(
            isinstance(item, str) and item.strip() for item in raw_checks
        ):
            raise ValueError("impact checks must be a string list")
        rules.append(
            ImpactRule(
                _identifier(row.get("id"), "impact rule id"),
                patterns,
                _strings(row.get("effects"), "impact effects"),
                tuple(item.strip() for item in raw_checks),
            )
        )
    _unique(rules, "impact rule")
    return tuple(rules), edges, checks


def load_contracts(root: pathlib.Path | None = None) -> Contracts:
    """Load and validate every Company OS registry."""
    directory = (root or pathlib.Path(__file__).resolve().parent).resolve()
    values = {
        name: _read_json(directory / filename)
        for name, filename in CONTRACT_FILES.items()
    }
    roles = _load_roles(values["roles"])
    workflows = _load_workflows(values["workflows"], roles)
    frameworks = _load_frameworks(values["frameworks"])
    rules, edges, checks = _load_impact(values["impact"])
    return Contracts(roles, workflows, frameworks, rules, edges, checks)


def _project_root(project: pathlib.Path) -> pathlib.Path:
    try:
        root = project.expanduser().resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"project directory is unavailable: {project}") from exc
    if not root.is_dir():
        raise ValueError(f"project directory is unavailable: {project}")
    return root


def _bounded_json(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        if not path.is_file() or path.stat().st_size > MAX_MARKER_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _dependency_names(package: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(field)
        if isinstance(values, dict):
            names.update(key for key in values if isinstance(key, str))
    return names


def _detector_matches(root: pathlib.Path, detector: dict[str, Any]) -> bool:
    candidate = (root / detector["path"]).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    if detector["kind"] == "path-exists":
        return candidate.exists()
    package = _bounded_json(candidate)
    return bool(package and set(detector["values"]) <= _dependency_names(package))


def inspect_project(project: pathlib.Path, contracts: Contracts) -> dict[str, Any]:
    """Detect project frameworks from bounded marker files without execution."""
    root = _project_root(project)
    detected = sorted(
        framework.id
        for framework in contracts.frameworks.values()
        if not framework.fallback
        and any(_detector_matches(root, detector) for detector in framework.detectors)
    )
    if not detected:
        detected = [
            framework.id
            for framework in contracts.frameworks.values()
            if framework.fallback
        ]
    return {
        "schema_version": 1,
        "project": root.name,
        "frameworks": detected,
    }


def _intent_words(intent: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", intent.lower()))


def _select_workflow(intent: str, contracts: Contracts) -> Workflow:
    normalized = _intent_words(intent)
    padded = f" {normalized} "
    ranked: list[tuple[int, int, str, Workflow]] = []
    for workflow in contracts.workflows.values():
        score = sum(
            1
            for keyword in workflow.keywords
            if f" {_intent_words(keyword)} " in padded
        )
        ranked.append((score, workflow.priority, workflow.id, workflow))
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    selected = ranked[0][3]
    if ranked[0][0] == 0:
        selected = contracts.workflows["feature-delivery"]
    return selected


def _skill_dict(skill: SkillRef) -> dict[str, str]:
    return {"package": skill.package, "skill": skill.skill}


def _qualified_roles(intent: str, workflow: Workflow) -> tuple[str, ...]:
    """Trim broad feature roles when intent clearly names one product area."""
    if workflow.id != "feature-delivery":
        return workflow.roles
    words = set(_intent_words(intent).split())
    backend = bool(words & {"api", "auth", "authentication", "backend", "database", "server"})
    frontend = bool(words & {"component", "dashboard", "design", "frontend", "page", "screen", "ui", "ux"})
    if backend and not frontend:
        return tuple(role for role in workflow.roles if role != "frontend-engineer")
    if frontend and not backend:
        return tuple(role for role in workflow.roles if role != "backend-engineer")
    return workflow.roles


def _intent_areas(intent: str) -> tuple[bool, bool]:
    words = set(_intent_words(intent).split())
    backend = bool(
        words & {"api", "auth", "authentication", "backend", "database", "server"}
    )
    frontend = bool(
        words
        & {
            "component",
            "dashboard",
            "design",
            "frontend",
            "page",
            "react",
            "screen",
            "ui",
            "ux",
        }
    )
    return backend, frontend


def _framework_relevant(framework_id: str, workflow: Workflow, intent: str) -> bool:
    backend, frontend = _intent_areas(intent)
    code_workflow = workflow.id in {
        "bugfix-delivery",
        "feature-delivery",
        "integration-delivery",
        "security-delivery",
    }
    if framework_id == "static-web":
        return workflow.id == "ui-delivery"
    if framework_id == "documentation":
        return workflow.id == "documentation-delivery"
    if framework_id in {"nextjs", "react"}:
        return workflow.id == "ui-delivery" or (code_workflow and not (backend and not frontend))
    if framework_id == "python":
        return code_workflow and not (frontend and not backend)
    return True


def plan_intent(
    intent: str, project: pathlib.Path, contracts: Contracts
) -> dict[str, Any]:
    """Return the smallest deterministic company route for an intent."""
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("intent cannot be empty")
    inspection = inspect_project(project, contracts)
    workflow = _select_workflow(intent, contracts)
    roles = _qualified_roles(intent, workflow)
    skills = set(workflow.skills)
    checks: set[str] = set()
    for role_id in roles:
        role_skills = contracts.roles[role_id].skills
        if workflow.id != "ui-delivery":
            role_skills = tuple(skill for skill in role_skills if skill.package != "ui-pack")
        skills.update(role_skills)
    for framework_id in inspection["frameworks"]:
        if _framework_relevant(framework_id, workflow, intent):
            framework = contracts.frameworks[framework_id]
            skills.update(framework.skills)
            checks.update(framework.checks)
    ordered_skills = sorted(skills)
    return {
        "schema_version": 1,
        "intent": intent.strip(),
        "project": inspection["project"],
        "workflow": workflow.id,
        "frameworks": inspection["frameworks"],
        "roles": list(roles),
        "stages": list(workflow.stages),
        "packages": sorted({skill.package for skill in ordered_skills}),
        "skills": [_skill_dict(skill) for skill in ordered_skills],
        "checks": sorted(checks),
    }


def _change_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("changed path must be relative")
    normalized = value.strip().replace("\\", "/")
    pure = pathlib.PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"changed path must be relative: {value}")
    return pure.as_posix()


def _effect_closure(initial: set[str], edges: dict[str, tuple[str, ...]]) -> set[str]:
    effects = set(initial)
    pending = deque(sorted(initial))
    while pending:
        current = pending.popleft()
        for target in edges.get(current, ()):
            if target not in effects:
                effects.add(target)
                pending.append(target)
    return effects


def calculate_impact(paths: list[str], contracts: Contracts) -> dict[str, Any]:
    """Calculate stable transitive impacts for repository-relative paths."""
    if not isinstance(paths, list) or not paths:
        raise ValueError("at least one changed path is required")
    changed = sorted({_change_path(path) for path in paths})
    matched: list[str] = []
    effects: set[str] = set()
    checks: set[str] = set()
    for rule in contracts.impact_rules:
        if any(
            fnmatch.fnmatchcase(path, pattern)
            for path in changed
            for pattern in rule.patterns
        ):
            matched.append(rule.id)
            effects.update(rule.effects)
            checks.update(rule.checks)
    effects = _effect_closure(effects, contracts.effect_edges)
    for effect in effects:
        checks.update(contracts.effect_checks.get(effect, ()))
    return {
        "schema_version": 1,
        "changed_paths": changed,
        "matched_rules": sorted(matched),
        "effects": sorted(effects),
        "checks": sorted(checks),
    }
