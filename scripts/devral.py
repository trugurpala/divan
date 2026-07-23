#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/handoff.py`."""
try:
    from handoff import *  # noqa: F403
    from handoff import main
except ModuleNotFoundError:
    from scripts.handoff import *  # noqa: F403
    from scripts.handoff import main

if __name__ == "__main__":
    raise SystemExit(main())
