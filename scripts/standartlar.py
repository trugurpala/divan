#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/standards.py`."""
try:
    from standards import *  # noqa: F403
    from standards import main
except ModuleNotFoundError:
    from scripts.standards import *  # noqa: F403
    from scripts.standards import main

if __name__ == "__main__":
    raise SystemExit(main())
