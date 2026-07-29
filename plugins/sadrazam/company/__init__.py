"""Compatibility package for the canonical :mod:`divan_runtime` package.

The public product remains Divan.  This import path is retained through v1 and
will not be removed before v2.
"""

from __future__ import annotations

import pathlib
import sys

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.compatibility import (  # noqa: E402
    CANONICAL_PACKAGE,
    LEGACY_PACKAGE,
    REMOVE_NO_EARLIER_THAN,
)

__all__ = ["CANONICAL_PACKAGE", "LEGACY_PACKAGE", "REMOVE_NO_EARLIER_THAN"]
