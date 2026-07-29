"""Internal helper for the pre-v0.17 ``company`` compatibility package."""
from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
import pathlib
import sys
from types import ModuleType
from typing import Any


def _source_spec(
    name: str,
    path: pathlib.Path,
    *,
    package_directory: pathlib.Path | None = None,
) -> importlib.machinery.ModuleSpec:
    search_locations = (
        [str(package_directory)] if package_directory is not None else None
    )
    spec = importlib.util.spec_from_file_location(
        name,
        path,
        submodule_search_locations=search_locations,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"legacy Divan cannot load canonical source: {path.name}")
    return spec


def _execute_exact_source(
    name: str,
    path: pathlib.Path,
    *,
    package_directory: pathlib.Path | None = None,
) -> ModuleType:
    spec = _source_spec(name, path, package_directory=package_directory)
    loader = spec.loader
    if loader is None:
        raise RuntimeError(f"legacy Divan cannot load canonical source: {path.name}")
    existing = sys.modules.get(name)
    module = (
        existing
        if isinstance(existing, ModuleType)
        else importlib.util.module_from_spec(spec)
    )
    backup = dict(module.__dict__) if isinstance(existing, ModuleType) else None
    template = importlib.util.module_from_spec(spec)
    module.__dict__.clear()
    module.__dict__.update(template.__dict__)
    sys.modules[name] = module
    try:
        loader.exec_module(module)
    except BaseException:
        if backup is None:
            sys.modules.pop(name, None)
        else:
            module.__dict__.clear()
            module.__dict__.update(backup)
            sys.modules[name] = module
        raise
    module_file = getattr(module, "__file__", None)
    if (
        not isinstance(module_file, str)
        or pathlib.Path(module_file).resolve() != path.resolve()
    ):
        raise RuntimeError(f"legacy Divan loaded unexpected source: {path.name}")
    return module


def _restore_package_children(package: ModuleType) -> None:
    prefix = f"{package.__name__}."
    for name, module in list(sys.modules.items()):
        suffix = name.removeprefix(prefix)
        if (
            name.startswith(prefix)
            and "." not in suffix
            and isinstance(module, ModuleType)
        ):
            setattr(package, suffix, module)


def _source_dependencies(path: pathlib.Path, runtime_root: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    dependencies: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 1 and node.module:
            dependencies.add(node.module.split(".", maxsplit=1)[0])
        elif node.level == 1:
            dependencies.update(alias.name for alias in node.names)
        elif node.level == 0 and node.module == "divan_runtime":
            dependencies.update(alias.name for alias in node.names)
    return sorted(
        name
        for name in dependencies
        if (runtime_root / f"{name}.py").is_file()
    )


def _bind_runtime_module(
    module_name: str,
    runtime_root: pathlib.Path,
    visiting: set[str],
) -> ModuleType:
    if module_name in visiting:
        raise RuntimeError("legacy Divan canonical imports contain a cycle")
    path = runtime_root / f"{module_name}.py"
    if not path.is_file():
        raise RuntimeError(f"legacy Divan canonical module is missing: {module_name}")
    visiting.add(module_name)
    try:
        for dependency in _source_dependencies(path, runtime_root):
            _bind_runtime_module(dependency, runtime_root, visiting)
        implementation = _execute_exact_source(
            f"divan_runtime.{module_name}", path
        )
        package = sys.modules.get("divan_runtime")
        if isinstance(package, ModuleType):
            setattr(package, module_name, implementation)
        return implementation
    finally:
        visiting.remove(module_name)


def expose(module_name: str, namespace: dict[str, Any]) -> ModuleType:
    """Expose one canonical runtime module through a legacy module path."""
    caller_file = namespace.get("__file__")
    if not isinstance(caller_file, str):
        raise RuntimeError("legacy Divan module has no source identity")
    plugin_root = pathlib.Path(caller_file).resolve().parent.parent
    runtime_root = (plugin_root / "divan_runtime").resolve()
    plugin_text = str(plugin_root)
    previous_path = list(sys.path)
    try:
        while plugin_text in sys.path:
            sys.path.remove(plugin_text)
        sys.path.insert(0, plugin_text)
        package = _execute_exact_source(
            "divan_runtime",
            runtime_root / "__init__.py",
            package_directory=runtime_root,
        )
        _restore_package_children(package)
        implementation = _bind_runtime_module(module_name, runtime_root, set())
        setattr(package, module_name, implementation)
    finally:
        sys.path[:] = previous_path
    namespace.update(
        {
            name: value
            for name, value in vars(implementation).items()
            if name not in {"__loader__", "__name__", "__package__", "__spec__"}
        }
    )
    caller_name = str(namespace["__name__"])
    if caller_name in sys.modules:
        sys.modules[caller_name] = implementation
    return implementation
