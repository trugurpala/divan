"""Repository-level loader for the canonical Divan runtime contracts."""
from __future__ import annotations

import contextlib
import importlib.util
import os
import pathlib
import stat
import sys
from collections.abc import Iterator
from types import ModuleType


def _runtime_module_names() -> list[str]:
    return [
        name
        for name in sys.modules
        if name == "divan_runtime" or name.startswith("divan_runtime.")
    ]


def _is_linklike(details: os.stat_result) -> bool:
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(details, "st_file_attributes", 0)
    return stat.S_ISLNK(details.st_mode) or bool(attributes & reparse)


def _checked_directory(path: pathlib.Path) -> os.stat_result:
    try:
        details = path.lstat()
    except OSError as error:
        raise ValueError("Divan runtime directory is unavailable") from error
    if _is_linklike(details):
        raise ValueError(
            "Divan runtime path cannot contain a symlink or reparse point"
        )
    if not stat.S_ISDIR(details.st_mode):
        raise ValueError("Divan runtime path must be a real directory")
    return details


def _runtime_directory(root: pathlib.Path) -> pathlib.Path:
    try:
        repository = root.resolve(strict=True)
    except OSError as error:
        raise ValueError("Divan repository root is unavailable") from error
    plugin_root = root / "plugins" / "sadrazam"
    runtime = plugin_root / "divan_runtime"
    before = None
    for directory in (root / "plugins", plugin_root, runtime):
        before = _checked_directory(directory)
    try:
        resolved = runtime.resolve(strict=True)
        relative = resolved.relative_to(repository)
    except (OSError, ValueError) as error:
        raise ValueError("Divan runtime escaped the repository root") from error
    expected = pathlib.Path("plugins") / "sadrazam" / "divan_runtime"
    if relative != expected:
        raise ValueError("Divan runtime escaped its canonical repository path")
    after = _checked_directory(runtime)
    if before is None or (before.st_dev, before.st_ino) != (
        after.st_dev,
        after.st_ino,
    ):
        raise ValueError("Divan runtime directory changed during validation")
    return resolved


def _source_details(path: pathlib.Path) -> os.stat_result:
    try:
        details = path.lstat()
    except OSError as error:
        raise ValueError(f"Divan runtime source is unavailable: {path.name}") from error
    if _is_linklike(details):
        raise ValueError(
            f"Divan runtime source cannot be a symlink or reparse point: {path.name}"
        )
    if not stat.S_ISREG(details.st_mode):
        raise ValueError(
            f"Divan runtime source must be a regular file: {path.name}"
        )
    return details


def _checked_source(runtime: pathlib.Path, name: str) -> pathlib.Path:
    path = runtime / name
    before = _source_details(path)
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(runtime)
    except (OSError, ValueError) as error:
        raise ValueError(
            f"Divan runtime source escaped the runtime root: {name}"
        ) from error
    if relative != pathlib.Path(name):
        raise ValueError(
            f"Divan runtime source escaped its canonical runtime path: {name}"
        )
    after = _source_details(path)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise ValueError(
            f"Divan runtime source changed during validation: {name}"
        )
    return resolved


def _load_source_module(
    name: str,
    path: pathlib.Path,
    *,
    package_directory: pathlib.Path | None = None,
) -> ModuleType:
    search_locations = (
        [str(package_directory)] if package_directory is not None else None
    )
    spec = importlib.util.spec_from_file_location(
        name,
        path,
        submodule_search_locations=search_locations,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Divan runtime source: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    if pathlib.Path(str(module.__file__)).resolve() != path.resolve():
        sys.modules.pop(name, None)
        raise RuntimeError(f"Divan runtime source escaped its root: {path.name}")
    return module


@contextlib.contextmanager
def _isolated_runtime(runtime: pathlib.Path) -> Iterator[tuple[ModuleType, ModuleType]]:
    previous_path = list(sys.path)
    previous = {
        name: sys.modules[name]
        for name in _runtime_module_names()
    }
    for name in previous:
        sys.modules.pop(name, None)
    try:
        _load_source_module(
            "divan_runtime",
            runtime / "__init__.py",
            package_directory=runtime,
        )
        engine = _load_source_module(
            "divan_runtime.engine", runtime / "engine.py"
        )
        kernel = _load_source_module(
            "divan_runtime.kernel", runtime / "kernel.py"
        )
        yield engine, kernel
    finally:
        for name in _runtime_module_names():
            sys.modules.pop(name, None)
        sys.modules.update(previous)
        sys.path[:] = previous_path


def validate(root: pathlib.Path) -> list[str]:
    """Return contract loading errors without importing project code."""
    try:
        runtime = _runtime_directory(root)
        required = ("__init__.py", "engine.py", "kernel.py")
        for name in required:
            _checked_source(runtime, name)
        with _isolated_runtime(runtime) as (engine, kernel):
            engine.load_contracts(runtime)
            kernel.load_architecture(runtime)
    except (
        ImportError,
        OSError,
        RuntimeError,
        SyntaxError,
        TypeError,
        ValueError,
    ) as exc:
        return [str(exc)]
    return []
