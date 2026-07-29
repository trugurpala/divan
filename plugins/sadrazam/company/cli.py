#!/usr/bin/env python3
"""Compatibility alias for :mod:`divan_runtime.cli`."""
import pathlib
import sys

DIRECTORY = pathlib.Path(__file__).resolve().parent
if str(DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DIRECTORY))
from _compat import expose  # noqa: E402

implementation = expose("cli", globals())

if __name__ == "__main__":
    raise SystemExit(implementation.main())  # type: ignore[attr-defined]
