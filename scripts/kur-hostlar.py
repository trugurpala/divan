#!/usr/bin/env python3
"""Deprecated compatibility wrapper; use `python scripts/divan.py`."""
from __future__ import annotations

import warnings

from host_lifecycle import *  # noqa: F403
from host_lifecycle import main

if __name__ == "__main__":
    warnings.warn(
        "scripts/kur-hostlar.py is deprecated; use scripts/divan.py",
        DeprecationWarning,
        stacklevel=1,
    )
    raise SystemExit(main())
