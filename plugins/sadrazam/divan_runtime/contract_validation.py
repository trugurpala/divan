"""Fail-closed validation for Divan's local runtime contracts."""
from __future__ import annotations

import ast
import json
import pathlib
import re
import stat
import sys
from typing import Any

MODULE_ID = re.compile(r"[a-z][a-z0-9_]*")
RUNTIME_PACKAGE = "divan_runtime"
RUNTIME_DATA_FILES = (
    "frameworks.json", "governance.json", "impact-graph.json", "modules.json",
    "roles.json", "workflows.json", "messages.json",
    "version.txt",
    "studio/index.html", "studio/studio.css", "studio/studio.js",
)
REQUIRED_MODULE_IDS = (
    "kernel", "governance", "council", "evidence", "project", "records",
    "providers", "release", "api",
)
MODULE_KEYS = {
    "id", "en", "tr", "python_modules", "capabilities", "depends_on", "required",
}
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_reparse_point(path: pathlib.Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError(f"runtime contract path is unreadable: {path.name}") from error
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & REPARSE_POINT)


def runtime_root(directory: pathlib.Path) -> pathlib.Path:
    candidate = directory.absolute()
    if _is_reparse_point(candidate):
        raise ValueError("runtime contract root cannot be a symlink or reparse point")
    try:
        root = candidate.resolve(strict=True)
    except OSError as error:
        raise ValueError("runtime contract root is unreadable") from error
    if not root.is_dir():
        raise ValueError("runtime contract root must be a directory")
    return root


def runtime_file(root: pathlib.Path, name: str) -> pathlib.Path:
    candidate = root / name
    if _is_reparse_point(candidate):
        raise ValueError(f"runtime file cannot be a symlink or reparse point: {name}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise ValueError(f"runtime file escapes its contract root: {name}") from error
    if not resolved.is_file():
        raise ValueError(f"runtime file is missing: {name}")
    return resolved


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid Divan runtime contract: {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"invalid Divan runtime contract schema: {path.name}")
    return value


def schema_version_one(value: object, filename: str) -> None:
    if type(value) is not int or value != 1:
        raise ValueError(f"{filename} must use schema version 1")


def label(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")
    return value


def strings(value: object, field: str, *, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(
            not isinstance(item, str) or not item or item != item.strip()
            for item in value
        )
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{field} must be a unique string list")
    return value


def _module_identifier(row: dict[str, Any], identifiers: set[str]) -> str:
    identifier = row["id"]
    if (
        not isinstance(identifier, str)
        or MODULE_ID.fullmatch(identifier) is None
        or identifier in identifiers
    ):
        raise ValueError("runtime module ids must be unique ASCII snake_case")
    label(row["en"], f"runtime module {identifier} en label")
    label(row["tr"], f"runtime module {identifier} tr label")
    if not isinstance(row["required"], bool):
        raise ValueError(f"runtime module {identifier} required must be boolean")
    return identifier


def _module_files(
    directory: pathlib.Path,
    identifier: str,
    names: list[str],
    owned: set[str],
) -> None:
    for module_name in names:
        if MODULE_ID.fullmatch(module_name) is None:
            raise ValueError(
                f"runtime module {identifier} has an invalid Python module"
            )
        if module_name in owned:
            raise ValueError(f"Python module is assigned more than once: {module_name}")
        runtime_file(directory, f"{module_name}.py")
        owned.add(module_name)


def _validated_module(
    directory: pathlib.Path,
    row: dict[str, Any],
    identifiers: set[str],
    owned_python_modules: set[str],
) -> dict[str, Any]:
    identifier = _module_identifier(row, identifiers)
    python_modules = strings(
        row["python_modules"], f"runtime module {identifier} python_modules"
    )
    _module_files(directory, identifier, python_modules, owned_python_modules)
    identifiers.add(identifier)
    return {
        "id": identifier,
        "en": row["en"],
        "tr": row["tr"],
        "python_modules": python_modules,
        "capabilities": strings(
            row["capabilities"], f"runtime module {identifier} capabilities"
        ),
        "depends_on": strings(
            row["depends_on"],
            f"runtime module {identifier} depends_on",
            allow_empty=True,
        ),
        "required": row["required"],
    }


def _validate_required_modules(modules: list[dict[str, Any]]) -> None:
    observed = tuple(str(row["id"]) for row in modules)
    if observed != REQUIRED_MODULE_IDS:
        raise ValueError("runtime must contain the canonical nine required modules")
    if any(row["required"] is not True for row in modules):
        raise ValueError("canonical runtime modules must be required")


def _validate_runtime_inventory(
    directory: pathlib.Path, modules: list[dict[str, Any]]
) -> None:
    runtime_file(directory, "__init__.py")
    for filename in RUNTIME_DATA_FILES:
        runtime_file(directory, filename)
    declared = {
        str(module_name)
        for row in modules
        for module_name in row["python_modules"]
    }
    discovered: set[str] = set()
    try:
        entries = tuple(directory.iterdir())
        nested_python = tuple(
            path
            for path in directory.rglob("*.py")
            if path.parent != directory
        )
    except OSError as error:
        raise ValueError("runtime contract root is unreadable") from error
    if nested_python:
        nested = ", ".join(
            sorted(path.relative_to(directory).as_posix() for path in nested_python)
        )
        raise ValueError(f"runtime Python modules must be top-level: {nested}")
    for entry in entries:
        if entry.suffix != ".py" or entry.name == "__init__.py":
            continue
        runtime_file(directory, entry.name)
        discovered.add(entry.stem)
    undeclared = sorted(discovered - declared)
    missing = sorted(declared - discovered)
    if undeclared:
        raise ValueError(
            f"runtime Python modules are undeclared: {', '.join(undeclared)}"
        )
    if missing:
        raise ValueError(f"runtime Python modules are missing: {', '.join(missing)}")


def _validate_dependencies(modules: list[dict[str, Any]]) -> None:
    identifiers = {str(row["id"]) for row in modules}
    graph = {
        str(row["id"]): [str(item) for item in row["depends_on"]]
        for row in modules
    }
    for identifier, dependencies in graph.items():
        unknown = sorted(set(dependencies) - identifiers)
        if unknown:
            raise ValueError(
                f"runtime module {identifier} has unknown dependencies: "
                f"{', '.join(unknown)}"
            )
        if identifier in dependencies:
            raise ValueError(f"runtime module {identifier} cannot depend on itself")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise ValueError("runtime module dependencies must be acyclic")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in graph[identifier]:
            visit(dependency)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(graph):
        visit(identifier)


def _absolute_import(
    module: str, names: list[str], internal: set[str], external: set[str]
) -> None:
    parts = module.split(".")
    top_level = parts[0]
    if top_level != RUNTIME_PACKAGE:
        if top_level not in sys.stdlib_module_names:
            external.add(top_level)
        return
    if len(parts) > 1:
        internal.add(parts[1])
    else:
        internal.update(name.split(".")[0] for name in names if name != "*")


def _dynamic_import_targets(tree: ast.AST, path: pathlib.Path) -> list[str]:
    dynamic_names = {"__import__", "import_module"} | {
        alias.asname or alias.name
        for candidate in ast.walk(tree)
        if isinstance(candidate, ast.ImportFrom) and candidate.level == 0
        for alias in candidate.names
        if (candidate.module, alias.name)
        in {("builtins", "__import__"), ("importlib", "import_module")}
    }
    targets: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        is_dynamic = (
            isinstance(function, ast.Name) and function.id in dynamic_names
        ) or (isinstance(function, ast.Attribute) and function.attr == "import_module")
        if not is_dynamic:
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            raise ValueError(f"runtime module uses unbounded dynamic import: {path.name}")
        target = node.args[0].value
        if not isinstance(target, str) or not target or target.startswith("."):
            raise ValueError(f"runtime module uses an invalid dynamic import: {path.name}")
        targets.append(target)
    return targets


def _source_imports(path: pathlib.Path) -> tuple[set[str], set[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        raise ValueError(f"runtime Python module is invalid: {path.name}") from error
    internal: set[str] = set()
    external: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _absolute_import(alias.name, [], internal, external)
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            if node.level == 0:
                _absolute_import(node.module or "", names, internal, external)
            elif node.level == 1:
                if node.module:
                    internal.add(node.module.split(".")[0])
                else:
                    internal.update(name.split(".")[0] for name in names if name != "*")
            else:
                raise ValueError(
                    f"runtime Python module uses an escaping relative import: {path.name}"
                )
    for target in _dynamic_import_targets(tree, path):
        _absolute_import(target, [], internal, external)
    return internal, external


def _validate_source_dependencies(
    directory: pathlib.Path,
    source_name: str,
    owner: str,
    declared_dependencies: set[str],
    module_owners: dict[str, str],
) -> None:
    path = runtime_file(directory, f"{source_name}.py")
    internal, external = _source_imports(path)
    if external:
        raise ValueError(
            f"runtime Python module {source_name} imports external dependencies: "
            f"{', '.join(sorted(external))}"
        )
    for imported in sorted(internal):
        imported_owner = module_owners.get(imported)
        if imported_owner is None:
            raise ValueError(
                f"runtime Python module {source_name} imports undeclared module: "
                f"{imported}"
            )
        if imported_owner != owner and imported_owner not in declared_dependencies:
            raise ValueError(
                f"runtime module {owner} must declare dependency on "
                f"{imported_owner} for import {source_name}->{imported}"
            )


def _validate_import_contracts(
    directory: pathlib.Path, modules: list[dict[str, Any]]
) -> None:
    module_owners = {
        str(module_name): str(row["id"])
        for row in modules
        for module_name in row["python_modules"]
    }
    dependencies = {
        str(row["id"]): {str(item) for item in row["depends_on"]}
        for row in modules
    }
    for source_name, owner in sorted(module_owners.items()):
        _validate_source_dependencies(
            directory,
            source_name,
            owner,
            dependencies[owner],
            module_owners,
        )
    _validate_source_dependencies(
        directory, "__init__", "api", dependencies["api"], module_owners
    )


def _validated_module_rows(
    directory: pathlib.Path, value: object
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("modules must be a non-empty list")
    modules: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    owned_python_modules: set[str] = set()
    for row in value:
        if not isinstance(row, dict) or set(row) != MODULE_KEYS:
            raise ValueError("each runtime module must use the canonical schema")
        modules.append(
            _validated_module(
                directory, row, identifiers, owned_python_modules
            )
        )
    _validate_required_modules(modules)
    _validate_runtime_inventory(directory, modules)
    _validate_dependencies(modules)
    _validate_import_contracts(directory, modules)
    return modules


def load_modules(directory: pathlib.Path) -> list[dict[str, Any]]:
    """Load and validate the complete nine-module runtime contract."""
    root = runtime_root(directory)
    contract = load_json(runtime_file(root, "modules.json"))
    if set(contract) != {"schema_version", "modules"}:
        raise ValueError("modules.json must use the canonical schema")
    schema_version_one(contract.get("schema_version"), "modules.json")
    return _validated_module_rows(root, contract["modules"])
