#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/catalog.py`."""
try:
    from catalog import *  # noqa: F403
    from catalog import main
except ModuleNotFoundError:
    from scripts.catalog import *  # noqa: F403
    from scripts.catalog import main

if __name__ == "__main__":
    raise SystemExit(main())
