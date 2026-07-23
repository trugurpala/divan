#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `scripts/upstream_watch.py`."""
try:
    from upstream_watch import *  # noqa: F403
    from upstream_watch import main
except ModuleNotFoundError:
    from scripts.upstream_watch import *  # noqa: F403
    from scripts.upstream_watch import main

if __name__ == "__main__":
    raise SystemExit(main())
