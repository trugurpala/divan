#!/usr/bin/env python3
"""Standalone entrypoint for the Divan Desktop bundled runtime.

The production Windows build freezes this tiny launcher with PyInstaller and
ships the canonical stdlib-only ``divan_runtime`` source tree as application
data.  Contract validation therefore keeps seeing the same real files that the
portable zipapp validates, while end users do not need a system Python install.
"""
from __future__ import annotations

import pathlib
import sys
from collections.abc import Sequence


def _runtime_parent() -> pathlib.Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return pathlib.Path(str(sys._MEIPASS)).resolve()
    root = pathlib.Path(__file__).resolve().parents[1]
    return (root / "plugins" / "sadrazam").resolve()


def main(argv: Sequence[str] | None = None) -> int:
    runtime_parent = _runtime_parent()
    runtime_package = runtime_parent / "divan_runtime"
    if not runtime_package.is_dir():
        print("ERROR: bundled Divan runtime is missing", file=sys.stderr)
        return 2
    if str(runtime_parent) not in sys.path:
        sys.path.insert(0, str(runtime_parent))
    from divan_runtime.cli import main as runtime_main

    arguments = list(sys.argv[1:] if argv is None else argv)
    return int(runtime_main(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
