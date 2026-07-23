#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/release.py`."""
try:
    from release import *  # noqa: F403
    from release import main
except ModuleNotFoundError:
    from scripts.release import *  # noqa: F403
    from scripts.release import main

if __name__ == "__main__":
    raise SystemExit(main())
