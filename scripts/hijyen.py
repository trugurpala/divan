#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/hygiene.py`."""
try:
    from hygiene import *  # noqa: F403
    from hygiene import main
except ModuleNotFoundError:
    from scripts.hygiene import *  # noqa: F403
    from scripts.hygiene import main

if __name__ == "__main__":
    raise SystemExit(main())
