"""Compatibility policy for pre-v0.17 Company OS import paths."""
from __future__ import annotations

LEGACY_PACKAGE = "company"
CANONICAL_PACKAGE = "divan_runtime"
REMOVE_NO_EARLIER_THAN = "2.0.0"

__all__ = ["CANONICAL_PACKAGE", "LEGACY_PACKAGE", "REMOVE_NO_EARLIER_THAN"]
