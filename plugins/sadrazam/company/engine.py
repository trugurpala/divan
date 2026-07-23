#!/usr/bin/env python3
"""Read-only project intelligence and impact routing for Divan Company OS."""
from __future__ import annotations

import fnmatch
import itertools
import json
import os
import pathlib
import re
import tomllib
import unicodedata
from collections import deque
from typing import Any, NamedTuple

MAX_MARKER_BYTES = 1024 * 1024
MAX_MARKER_NESTING = 32
MAX_PROJECT_DEPTH = 4
MAX_PROJECT_DIRECTORIES = 128
MAX_DIRECTORY_ENTRIES = 256
IGNORED_PROJECT_DIRECTORIES = frozenset(
    {
        ".cache",
        ".git",
        ".gradle",
        ".hg",
        ".mypy_cache",
        ".next",
        ".nuxt",
        ".output",
        ".parcel-cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svelte-kit",
        ".svn",
        ".tox",
        ".turbo",
        ".venv",
        ".vercel",
        "__pycache__",
        "bin",
        "build",
        "cache",
        "coverage",
        "dist",
        "node_modules",
        "obj",
        "out",
        "target",
        "vendor",
        "venv",
    }
)
WORKSPACE_MANIFESTS = frozenset(
    {
        "Cargo.toml",
        "go.mod",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
    }
)
NODE_LOCKFILES = {
    "bun": ("bun.lock", "bun.lockb"),
    "npm": ("package-lock.json", "npm-shrinkwrap.json"),
    "pnpm": ("pnpm-lock.yaml",),
    "yarn": ("yarn.lock",),
}
TARGET_EVIDENCE = {
    "verified": ("project inspection", "project-native verification"),
    "previewed": (
        "project inspection",
        "project-native verification",
        "preview URL",
        "browser verification",
    ),
    "released": (
        "project inspection",
        "project-native verification",
        "provider release evidence",
        "live readback",
    ),
    "observed": (
        "project inspection",
        "project-native verification",
        "provider release evidence",
        "live readback",
        "observation evidence",
    ),
}
CONTRACT_FILES = {
    "roles": "roles.json",
    "workflows": "workflows.json",
    "frameworks": "frameworks.json",
    "impact": "impact-graph.json",
}
PACKAGE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGE_SCRIPT_NAME = re.compile(r"^(?!-)[A-Za-z0-9:_-]+$")
PYTHON_DISTRIBUTION = re.compile(
    r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)"
)
PYTHON_VERSION_SPECIFIER = re.compile(
    r"(?P<operator>===|==|!=|~=|<=|>=|<|>)\s*"
    r"(?P<version>[^\s;()]+)"
)
PYTHON_VERSION = re.compile(
    r"""
    v?
    (?:[0-9]+!)?
    (?P<release>[0-9]+(?:\.[0-9]+)*)
    (?:
        [-_.]?
        (?:alpha|beta|preview|pre|rc|a|b|c)
        (?:[-_.]?[0-9]+)?
    )?
    (?:
        (?:-[0-9]+)
        |
        (?:[-_.]?(?:post|rev|r)(?:[-_.]?[0-9]+)?)
    )?
    (?:[-_.]?dev(?:[-_.]?[0-9]+)?)?
    (?:\+(?P<local>[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*))?
    """,
    re.IGNORECASE | re.VERBOSE,
)
PYTHON_RELEASE_WILDCARD = re.compile(
    r"v?(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*\.\*",
    re.IGNORECASE,
)
PYTHON_MARKER_TOKEN = re.compile(
    r"\s*(?:"
    r"(?P<parenthesis>[()])|"
    r"(?P<string>'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")|"
    r"(?P<operator>not\s+in|===|==|!=|~=|<=|>=|<|>|\bin\b)|"
    r"(?P<word>[A-Za-z_][A-Za-z0-9_]*)"
    r")"
)
PYTHON_MARKER_VARIABLES = frozenset(
    {
        "dependency_groups",
        "extra",
        "extras",
        "implementation_name",
        "implementation_version",
        "os_name",
        "platform_machine",
        "platform_python_implementation",
        "platform_release",
        "platform_system",
        "platform_version",
        "python_full_version",
        "python_version",
        "sys_platform",
    }
)


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
    providers: tuple[str, ...]
    required_evidence: tuple[str, ...]


class Framework(NamedTuple):
    id: str
    label: dict[str, str]
    fallback: bool
    detectors: tuple[dict[str, Any], ...]
    skills: tuple[SkillRef, ...]
    checks: tuple[str, ...]
    project_types: tuple[str, ...]


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


def _string_list(
    value: Any, context: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{context} must be a string list")
    if not allow_empty and not value:
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
                _strings(row.get("providers"), "workflow providers"),
                _strings(row.get("required_evidence"), "workflow evidence"),
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
                "directory-exists",
                "file-exists",
                "package-json-dependency",
                "python-dependency",
            }:
                raise ValueError("framework detector is invalid")
            normalized = dict(detector)
            normalized["path"] = _safe_relative(detector.get("path"), "detector")
            if detector["kind"] in {
                "package-json-dependency",
                "python-dependency",
            }:
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
                _string_list(
                    row.get("project_types"),
                    "framework project types",
                    allow_empty=True,
                ),
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


def _bounded_file(path: pathlib.Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size <= MAX_MARKER_BYTES
    except OSError:
        return False


def _bounded_json(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        if not _bounded_file(path):
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _bounded_text(path: pathlib.Path) -> str | None:
    try:
        if not _bounded_file(path):
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _dependency_names(package: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(field)
        if isinstance(values, dict):
            names.update(key for key in values if isinstance(key, str))
    return names


def _is_project_contained(
    root: pathlib.Path, resolved_candidate: pathlib.Path
) -> bool:
    try:
        resolved_candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _contained_marker(
    root: pathlib.Path, workspace: pathlib.Path, relative: str
) -> pathlib.Path | None:
    candidate = workspace / relative
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    return resolved if _is_project_contained(root, resolved) else None


def _normalized_distribution(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).casefold()


def _valid_marker(value: str) -> bool:
    tokens: list[tuple[str, str]] = []
    position = 0
    nesting = 0
    while position < len(value):
        match = PYTHON_MARKER_TOKEN.match(value, position)
        if match is None:
            return False
        kind = match.lastgroup
        token = match.group(kind) if kind is not None else ""
        if kind == "word" and token not in {
            "and",
            "or",
            *PYTHON_MARKER_VARIABLES,
        }:
            return False
        if kind == "parenthesis":
            nesting += 1 if token == "(" else -1
            if nesting < 0 or nesting > MAX_MARKER_NESTING:
                return False
        tokens.append((kind or "", token))
        position = match.end()
    if nesting != 0:
        return False

    index = 0

    def parse_operand() -> bool:
        nonlocal index
        if index >= len(tokens):
            return False
        kind, token = tokens[index]
        if kind == "string" or (
            kind == "word" and token in PYTHON_MARKER_VARIABLES
        ):
            index += 1
            return True
        return False

    def parse_comparison() -> bool:
        nonlocal index
        if not parse_operand() or index >= len(tokens):
            return False
        if tokens[index][0] != "operator":
            return False
        index += 1
        return parse_operand()

    def parse_factor() -> bool:
        nonlocal index
        if index < len(tokens) and tokens[index] == ("parenthesis", "("):
            index += 1
            if not parse_expression():
                return False
            if index >= len(tokens) or tokens[index] != (
                "parenthesis",
                ")",
            ):
                return False
            index += 1
            return True
        return parse_comparison()

    def parse_term() -> bool:
        nonlocal index
        if not parse_factor():
            return False
        while index < len(tokens) and tokens[index] == ("word", "and"):
            index += 1
            if not parse_factor():
                return False
        return True

    def parse_expression() -> bool:
        nonlocal index
        if not parse_term():
            return False
        while index < len(tokens) and tokens[index] == ("word", "or"):
            index += 1
            if not parse_term():
                return False
        return True

    try:
        return bool(tokens) and parse_expression() and index == len(tokens)
    except RecursionError:
        return False


def _valid_version_specifiers(value: str) -> bool:
    parts = value.split(",")
    if not parts:
        return False
    for part in parts:
        specifier = PYTHON_VERSION_SPECIFIER.fullmatch(part.strip())
        if specifier is None:
            return False
        operator = specifier.group("operator")
        version = specifier.group("version")
        if operator == "===":
            continue
        if PYTHON_RELEASE_WILDCARD.fullmatch(version) is not None:
            if operator not in {"==", "!="}:
                return False
            continue
        parsed = PYTHON_VERSION.fullmatch(version)
        if parsed is None:
            return False
        if parsed.group("local") is not None and operator not in {"==", "!="}:
            return False
        if operator == "~=" and "." not in parsed.group("release"):
            return False
    return True


def _requirement_name(value: str) -> str | None:
    requirement = value.strip()
    match = PYTHON_DISTRIBUTION.match(requirement)
    if match is None:
        return None
    remainder = requirement[match.end() :].strip()
    if remainder.startswith("["):
        close = remainder.find("]")
        if close < 0:
            return None
        extras = remainder[1:close].split(",")
        if not extras or any(
            PYTHON_DISTRIBUTION.fullmatch(extra.strip()) is None
            for extra in extras
        ):
            return None
        remainder = remainder[close + 1 :].strip()
    if not remainder:
        return _normalized_distribution(match.group(1))
    if remainder.startswith("("):
        close = remainder.find(")")
        if close < 0 or "(" in remainder[1:close]:
            return None
        specifiers = remainder[1:close].strip()
        suffix = remainder[close + 1 :].strip()
        valid = _valid_version_specifiers(specifiers)
        if suffix:
            valid = (
                valid
                and suffix.startswith(";")
                and _valid_marker(suffix[1:].strip())
            )
    elif remainder.startswith(";"):
        valid = _valid_marker(remainder[1:].strip())
    elif remainder.startswith("@"):
        reference, separator, marker = remainder[1:].partition(";")
        reference = reference.strip()
        valid = bool(reference) and not any(
            character.isspace() for character in reference
        )
        if separator:
            valid = valid and _valid_marker(marker.strip())
    else:
        specifiers, separator, marker = remainder.partition(";")
        valid = _valid_version_specifiers(specifiers.strip())
        if separator:
            valid = valid and _valid_marker(marker.strip())
    return _normalized_distribution(match.group(1)) if valid else None


def _bounded_toml(path: pathlib.Path) -> dict[str, Any] | None:
    text = _bounded_text(path)
    if text is None:
        return None
    try:
        value = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _pyproject_dependency_names(value: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    project = value.get("project")
    if isinstance(project, dict):
        groups: list[Any] = [project.get("dependencies")]
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            groups.extend(optional.values())
        for group in groups:
            if isinstance(group, list):
                names.update(
                    name
                    for item in group
                    if isinstance(item, str)
                    if (name := _requirement_name(item)) is not None
                )
    tool = value.get("tool")
    poetry = tool.get("poetry") if isinstance(tool, dict) else None
    if isinstance(poetry, dict):
        tables: list[Any] = [
            poetry.get("dependencies"),
            poetry.get("dev-dependencies"),
        ]
        groups = poetry.get("group")
        if isinstance(groups, dict):
            tables.extend(
                group.get("dependencies")
                for group in groups.values()
                if isinstance(group, dict)
            )
        for table in tables:
            if isinstance(table, dict):
                names.update(
                    _normalized_distribution(name)
                    for name in table
                    if isinstance(name, str) and name.casefold() != "python"
                )
    return names


def _python_dependency_names(path: pathlib.Path) -> set[str]:
    if path.name == "pyproject.toml":
        value = _bounded_toml(path)
        return _pyproject_dependency_names(value) if value else set()
    if path.name != "requirements.txt":
        return set()
    text = _bounded_text(path)
    if text is None:
        return set()
    names: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        line = re.split(r"\s+#", line, maxsplit=1)[0]
        name = _requirement_name(line)
        if name is not None:
            names.add(name)
    return names


def _detector_matches(
    root: pathlib.Path, workspace: pathlib.Path, detector: dict[str, Any]
) -> bool:
    candidate = _contained_marker(root, workspace, detector["path"])
    if candidate is None:
        return False
    if detector["kind"] == "directory-exists":
        return candidate.is_dir()
    if detector["kind"] == "file-exists":
        return _bounded_file(candidate)
    if detector["kind"] == "python-dependency":
        dependencies = _python_dependency_names(candidate)
        return {
            _normalized_distribution(value) for value in detector["values"]
        } <= dependencies
    package = _bounded_json(candidate)
    return bool(package and set(detector["values"]) <= _dependency_names(package))


def _directory_name_key(name: str) -> tuple[str, str]:
    return name.casefold(), name


def _bounded_directory_entries(
    root: pathlib.Path, directory: pathlib.Path
) -> list[os.DirEntry[str]]:
    try:
        with os.scandir(directory) as iterator:
            entries = list(
                itertools.islice(iterator, MAX_DIRECTORY_ENTRIES + 1)
            )
    except OSError:
        return []
    if len(entries) > MAX_DIRECTORY_ENTRIES:
        relative = _relative_path(root, directory)
        raise ValueError(f"directory entry limit exceeded: {relative}")
    return sorted(entries, key=lambda entry: _directory_name_key(entry.name))


def _project_directories(root: pathlib.Path) -> list[pathlib.Path]:
    """Return a deterministic, project-contained depth-first traversal."""
    directories: list[pathlib.Path] = []
    pending: list[tuple[pathlib.Path, int]] = [(root, 0)]
    while pending and len(directories) < MAX_PROJECT_DIRECTORIES:
        directory, depth = pending.pop()
        try:
            resolved = directory.resolve()
            resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        if directory.is_symlink() or not resolved.is_dir():
            continue
        directories.append(resolved)
        if depth >= MAX_PROJECT_DEPTH:
            continue
        children: list[pathlib.Path] = []
        for entry in _bounded_directory_entries(root, resolved):
            if entry.name.casefold() in IGNORED_PROJECT_DIRECTORIES:
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    children.append(pathlib.Path(entry.path))
            except OSError:
                continue
        pending.extend(
            (child, depth + 1) for child in reversed(children)
        )
    return directories


def _relative_path(root: pathlib.Path, path: pathlib.Path) -> str:
    relative = path.relative_to(root).as_posix()
    return relative or "."


def _workspace_roots(
    root: pathlib.Path, directories: list[pathlib.Path]
) -> list[pathlib.Path]:
    workspaces = [root]
    for directory in directories:
        if directory == root:
            continue
        if any(
            (candidate := _contained_marker(root, directory, marker)) is not None
            and _bounded_file(candidate)
            for marker in WORKSPACE_MANIFESTS
        ):
            workspaces.append(directory)
    return sorted(
        set(workspaces),
        key=lambda path: _directory_name_key(_relative_path(root, path)),
    )


def _package_manager_resolution(
    root: pathlib.Path,
    workspace: pathlib.Path,
    package: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None, bool]:
    raw_declared = package.get("packageManager") if package else None
    declared = None
    invalid_declared = None
    if isinstance(raw_declared, str) and raw_declared.strip():
        candidate = raw_declared.partition("@")[0].strip().casefold()
        if candidate in NODE_LOCKFILES:
            declared = candidate
        else:
            invalid_declared = candidate
    lockfile_managers: list[str] = []
    for manager, lockfiles in NODE_LOCKFILES.items():
        if any(
            (candidate := _contained_marker(root, workspace, lockfile)) is not None
            and _bounded_file(candidate)
            for lockfile in lockfiles
        ):
            lockfile_managers.append(manager)
    lockfile_managers.sort()
    relative = _relative_path(root, workspace)
    if invalid_declared is not None:
        return (
            None,
            {
                "workspace": relative,
                "declared": invalid_declared,
                "lockfile_managers": lockfile_managers,
                "selected": None,
                "reason": "invalid-declaration",
            },
            True,
        )
    if declared is not None:
        conflict = None
        if any(manager != declared for manager in lockfile_managers):
            conflict = {
                "workspace": relative,
                "declared": declared,
                "lockfile_managers": lockfile_managers,
                "selected": declared,
                "reason": "declaration-lockfile-mismatch",
            }
        return declared, conflict, True
    if len(lockfile_managers) > 1:
        return (
            None,
            {
                "workspace": relative,
                "declared": None,
                "lockfile_managers": lockfile_managers,
                "selected": None,
                "reason": "multiple-lockfiles",
            },
            True,
        )
    if lockfile_managers:
        return lockfile_managers[0], None, True
    return None, None, False


def _nearest_workspace_manager(
    workspace: pathlib.Path,
    resolved_managers: dict[pathlib.Path, str | None],
) -> str | None:
    ancestors = [
        (len(candidate.parts), manager)
        for candidate, manager in resolved_managers.items()
        if candidate != workspace and workspace.is_relative_to(candidate)
    ]
    return max(ancestors, default=(0, None), key=lambda row: row[0])[1]


def _command_row(
    workspace: str, manager: str, name: str, command: str
) -> dict[str, str]:
    return {
        "workspace": workspace,
        "manager": manager,
        "name": name,
        "command": command,
    }


def _native_commands(
    root: pathlib.Path,
    workspace: pathlib.Path,
    package: dict[str, Any] | None,
    manager: str | None,
) -> list[dict[str, str]]:
    relative = _relative_path(root, workspace)
    commands: list[dict[str, str]] = []
    scripts = package.get("scripts") if package else None
    if isinstance(scripts, dict):
        names = sorted(
            name
            for name, value in scripts.items()
            if isinstance(name, str)
            and name.strip()
            and PACKAGE_SCRIPT_NAME.fullmatch(name)
            and isinstance(value, str)
            and value.strip()
        )
        if manager is not None:
            commands.extend(
                _command_row(
                    relative,
                    manager,
                    name,
                    f"{manager} run {name}",
                )
                for name in names
            )
    python_markers = ("pyproject.toml", "requirements.txt", "setup.py")
    if any(
        (candidate := _contained_marker(root, workspace, marker)) is not None
        and _bounded_text(candidate) is not None
        for marker in python_markers
    ):
        commands.append(
            _command_row(
                relative, "python", "test", "python -m unittest discover"
            )
        )
    go_mod = _contained_marker(root, workspace, "go.mod")
    if go_mod is not None and _bounded_text(go_mod) is not None:
        commands.append(_command_row(relative, "go", "test", "go test ./..."))
    cargo = _contained_marker(root, workspace, "Cargo.toml")
    if cargo is not None and _bounded_text(cargo) is not None:
        commands.append(_command_row(relative, "cargo", "test", "cargo test"))
    return commands


def _framework_ids(
    root: pathlib.Path,
    workspace: pathlib.Path,
    contracts: Contracts,
) -> list[str]:
    return sorted(
        framework.id
        for framework in contracts.frameworks.values()
        if not framework.fallback
        and any(
            _detector_matches(root, workspace, detector)
            for detector in framework.detectors
        )
    )


def _bounded_marker_exists(
    root: pathlib.Path, workspace: pathlib.Path, relative: str
) -> bool:
    candidate = _contained_marker(root, workspace, relative)
    return candidate is not None and _bounded_file(candidate)


def _python_project_types(
    root: pathlib.Path,
    workspace: pathlib.Path,
) -> set[str]:
    has_application = False
    has_library = False
    project_name = None
    pyproject_path = _contained_marker(root, workspace, "pyproject.toml")
    pyproject = (
        _bounded_toml(pyproject_path) if pyproject_path is not None else None
    )
    if pyproject:
        project = pyproject.get("project")
        if isinstance(project, dict):
            if isinstance(project.get("name"), str) and project["name"].strip():
                project_name = project["name"].strip()
            if (
                isinstance(project.get("entry-points"), dict)
                and project["entry-points"]
            ):
                has_library = True
            if any(
                isinstance(project.get(field), dict) and project.get(field)
                for field in ("gui-scripts", "scripts")
            ):
                has_application = True
        build_system = pyproject.get("build-system")
        if isinstance(build_system, dict) and build_system:
            has_library = True
        tool = pyproject.get("tool")
        poetry = tool.get("poetry") if isinstance(tool, dict) else None
        if isinstance(poetry, dict):
            if (
                project_name is None
                and isinstance(poetry.get("name"), str)
                and poetry["name"].strip()
            ):
                project_name = poetry["name"].strip()
            if isinstance(poetry.get("packages"), list) and poetry["packages"]:
                has_library = True
            if isinstance(poetry.get("scripts"), dict) and poetry["scripts"]:
                has_application = True
        setuptools = tool.get("setuptools") if isinstance(tool, dict) else None
        if isinstance(setuptools, dict) and any(
            field in setuptools for field in ("packages", "py-modules")
        ):
            has_library = True
    if _bounded_marker_exists(root, workspace, "setup.py"):
        has_library = True
    if _bounded_marker_exists(root, workspace, "__main__.py"):
        has_application = True
    if project_name is not None:
        package_name = re.sub(r"[-.]+", "_", project_name).casefold()
        package_directories = (package_name, f"src/{package_name}")
        if any(
            _bounded_marker_exists(root, workspace, f"{relative}/__main__.py")
            for relative in package_directories
        ):
            has_application = True
        if any(
            _bounded_marker_exists(root, workspace, f"{relative}/__init__.py")
            for relative in package_directories
        ):
            has_library = True
    if has_application:
        return {"application"}
    return {"library"} if has_library else set()


def _go_project_types(
    root: pathlib.Path, workspace: pathlib.Path
) -> set[str]:
    has_main = _bounded_marker_exists(root, workspace, "main.go")
    cmd = _contained_marker(root, workspace, "cmd")
    if has_main or (cmd is not None and cmd.is_dir()):
        return {"application"}
    return {"library"}


def _rust_project_types(
    root: pathlib.Path, workspace: pathlib.Path
) -> set[str]:
    project_types: set[str] = set()
    if _bounded_marker_exists(root, workspace, "src/main.rs"):
        project_types.add("application")
    if _bounded_marker_exists(root, workspace, "src/lib.rs"):
        project_types.add("library")
    cargo_path = _contained_marker(root, workspace, "Cargo.toml")
    cargo = _bounded_toml(cargo_path) if cargo_path is not None else None
    if cargo:
        if isinstance(cargo.get("bin"), list) and cargo["bin"]:
            project_types.add("application")
        if isinstance(cargo.get("lib"), dict):
            project_types.add("library")
    return project_types


def _workspace_project_types(
    root: pathlib.Path,
    workspace: pathlib.Path,
    package: dict[str, Any] | None,
    frameworks: list[str],
    contracts: Contracts,
) -> set[str]:
    project_types = {
        project_type
        for framework_id in frameworks
        for project_type in contracts.frameworks[framework_id].project_types
    }
    if package:
        if any(key in package for key in ("exports", "main", "module", "types")):
            project_types.add("library")
        scripts = package.get("scripts")
        if isinstance(scripts, dict) and {
            "build",
            "dev",
            "serve",
            "start",
        } & set(scripts):
            project_types.add("application")
        dependencies = _dependency_names(package)
        if dependencies & {"express", "fastify", "hapi", "koa", "nestjs"}:
            project_types.add("service")
    if "python" in frameworks:
        python_types = _python_project_types(root, workspace)
        if not {"application", "service"} & project_types:
            project_types.update(python_types)
        elif "application" in python_types:
            project_types.add("application")
    if "go" in frameworks:
        project_types.update(_go_project_types(root, workspace))
    if "rust" in frameworks:
        project_types.update(_rust_project_types(root, workspace))
    return project_types


def inspect_project(project: pathlib.Path, contracts: Contracts) -> dict[str, Any]:
    """Detect bounded manifest profiles without executing target project code."""
    root = _project_root(project)
    directories = _project_directories(root)
    workspaces = _workspace_roots(root, directories)
    workspace_rows: list[dict[str, Any]] = []
    commands: list[dict[str, str]] = []
    package_manager_conflicts: list[dict[str, Any]] = []
    detected: set[str] = set()
    project_types: set[str] = set()
    package_managers: set[str] = set()
    root_declares_workspaces = False
    resolved_managers: dict[pathlib.Path, str | None] = {}
    for workspace in workspaces:
        package_path = _contained_marker(root, workspace, "package.json")
        has_package_manifest = (
            package_path is not None and _bounded_file(package_path)
        )
        package = _bounded_json(package_path) if has_package_manifest else None
        if workspace == root and package and package.get("workspaces"):
            root_declares_workspaces = True
        manager, conflict, has_direct_evidence = _package_manager_resolution(
            root, workspace, package
        )
        if has_package_manifest and not has_direct_evidence:
            manager = _nearest_workspace_manager(workspace, resolved_managers)
        if has_package_manifest:
            resolved_managers[workspace] = manager
        if conflict is not None:
            package_manager_conflicts.append(conflict)
        frameworks = _framework_ids(root, workspace, contracts)
        workspace_types = _workspace_project_types(
            root,
            workspace,
            package,
            frameworks,
            contracts,
        )
        workspace_commands = _native_commands(root, workspace, package, manager)
        relative = _relative_path(root, workspace)
        workspace_rows.append(
            {
                "path": relative,
                "frameworks": frameworks,
                "project_types": sorted(workspace_types),
                "package_managers": [manager] if manager is not None else [],
            }
        )
        detected.update(frameworks)
        project_types.update(workspace_types)
        if manager is not None:
            package_managers.add(manager)
        commands.extend(workspace_commands)
    if not detected:
        fallback = next(
            framework
            for framework in contracts.frameworks.values()
            if framework.fallback
        )
        detected.add(fallback.id)
        project_types.update(fallback.project_types)
        workspace_rows[0]["frameworks"] = [fallback.id]
        workspace_rows[0]["project_types"] = sorted(project_types)
    if len(workspaces) > 1 or root_declares_workspaces:
        project_types.add("monorepo")
    commands.sort(
        key=lambda row: (
            row["workspace"],
            row["manager"],
            row["name"],
            row["command"],
        )
    )
    return {
        "schema_version": 2,
        "project": root.name,
        "frameworks": sorted(detected),
        "project_types": sorted(project_types),
        "workspaces": workspace_rows,
        "package_managers": sorted(package_managers),
        "package_manager_conflicts": package_manager_conflicts,
        "commands": commands,
    }


def _intent_words(intent: str) -> str:
    normalized = unicodedata.normalize("NFKC", intent).casefold()
    normalized = normalized.replace("\N{COMBINING DOT ABOVE}", "").replace(
        "\N{LATIN SMALL LETTER DOTLESS I}", "i"
    )
    return " ".join(
        "".join(character if character.isalnum() else " " for character in normalized)
        .split()
    )


def _phrase_spans(
    words: list[str], phrase: tuple[str, ...]
) -> list[tuple[int, int]]:
    width = len(phrase)
    return [
        (index, index + width)
        for index in range(len(words) - width + 1)
        if tuple(words[index : index + width]) == phrase
    ]


def _rank_workflows(intent: str, contracts: Contracts) -> list[Workflow]:
    words = _intent_words(intent).split()
    candidates: list[tuple[int, int, int, str, str, Workflow]] = []
    for workflow in contracts.workflows.values():
        for keyword in workflow.keywords:
            phrase = tuple(_intent_words(keyword).split())
            for start, end in _phrase_spans(words, phrase):
                candidates.append(
                    (
                        -len(phrase),
                        start,
                        -workflow.priority,
                        workflow.id,
                        keyword,
                        workflow,
                    )
                )
    occupied: set[int] = set()
    scores: dict[str, int] = {}
    for negative_width, start, _, _, _, workflow in sorted(candidates):
        end = start - negative_width
        span = set(range(start, end))
        if span & occupied:
            continue
        occupied.update(span)
        scores[workflow.id] = scores.get(workflow.id, 0) + 1
    ranked: list[tuple[int, int, str, Workflow]] = []
    for workflow in contracts.workflows.values():
        score = scores.get(workflow.id, 0)
        if score:
            ranked.append((score, workflow.priority, workflow.id, workflow))
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    if not ranked:
        return [contracts.workflows["feature-delivery"]]
    return [row[3] for row in ranked]


def _select_workflow(intent: str, contracts: Contracts) -> Workflow:
    return _rank_workflows(intent, contracts)[0]


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
        "testing-delivery",
    }
    if framework_id == "static-web":
        return workflow.id in {"deployment-delivery", "seo-delivery", "ui-delivery"}
    if framework_id == "documentation":
        return workflow.id in {"documentation-delivery", "seo-delivery"}
    if framework_id in {
        "astro",
        "expo",
        "nextjs",
        "nuxt",
        "react",
        "react-native",
        "svelte",
        "sveltekit",
        "vite",
        "vue",
    }:
        return workflow.id in {
            "deployment-delivery",
            "seo-delivery",
            "testing-delivery",
            "ui-delivery",
        } or (code_workflow and not (backend and not frontend))
    if framework_id in {"django", "fastapi", "go", "python", "rust"}:
        return workflow.id in {
            "deployment-delivery",
            "testing-delivery",
        } or (code_workflow and not (frontend and not backend))
    return True


def plan_intent(
    intent: str,
    project: pathlib.Path,
    contracts: Contracts,
    target: str = "verified",
) -> dict[str, Any]:
    """Return the smallest deterministic company route for an intent."""
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("intent cannot be empty")
    if target not in TARGET_EVIDENCE:
        raise ValueError(
            f"target must be one of: {', '.join(sorted(TARGET_EVIDENCE))}"
        )
    inspection = inspect_project(project, contracts)
    workflows = _rank_workflows(intent, contracts)
    workflow = workflows[0]
    roles: list[str] = []
    stages: list[str] = []
    for matched_workflow in workflows:
        for role_id in _qualified_roles(intent, matched_workflow):
            if role_id not in roles:
                roles.append(role_id)
        for stage in matched_workflow.stages:
            if stage not in stages:
                stages.append(stage)
    skills = {
        skill
        for matched_workflow in workflows
        for skill in matched_workflow.skills
    }
    checks: set[str] = set()
    for role_id in roles:
        role_skills = contracts.roles[role_id].skills
        if not any(row.id == "ui-delivery" for row in workflows):
            role_skills = tuple(skill for skill in role_skills if skill.package != "ui-pack")
        skills.update(role_skills)
    for framework_id in inspection["frameworks"]:
        if any(
            _framework_relevant(framework_id, matched_workflow, intent)
            for matched_workflow in workflows
        ):
            framework = contracts.frameworks[framework_id]
            skills.update(framework.skills)
            checks.update(framework.checks)
    checks.update(row["command"] for row in inspection["commands"])
    ordered_skills = sorted(skills)
    providers = sorted(
        {
            provider
            for matched_workflow in workflows
            for provider in matched_workflow.providers
        }
    )
    required_evidence = sorted(
        {
            *TARGET_EVIDENCE[target],
            *(
                evidence
                for matched_workflow in workflows
                for evidence in matched_workflow.required_evidence
            ),
        }
    )
    return {
        "schema_version": 2,
        "intent": intent.strip(),
        "project": inspection["project"],
        "workflow": workflow.id,
        "primary_workflow": workflow.id,
        "workflows": [row.id for row in workflows],
        "providers": providers,
        "required_evidence": required_evidence,
        "frameworks": inspection["frameworks"],
        "project_types": inspection["project_types"],
        "workspaces": inspection["workspaces"],
        "package_managers": inspection["package_managers"],
        "package_manager_conflicts": inspection["package_manager_conflicts"],
        "commands": inspection["commands"],
        "roles": roles,
        "stages": stages,
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
    classified_paths: set[str] = set()
    effects: set[str] = set()
    checks: set[str] = set()
    for rule in contracts.impact_rules:
        rule_paths = {
            path
            for path in changed
            for pattern in rule.patterns
            if fnmatch.fnmatchcase(path, pattern)
        }
        if rule_paths:
            matched.append(rule.id)
            classified_paths.update(rule_paths)
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
        "unclassified_paths": sorted(set(changed) - classified_paths),
    }
