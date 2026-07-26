"""Shared transaction boundary for Project OS lifecycle mutations.

The proven init engine remains the compatibility implementation. Lifecycle
callers depend on this narrow façade so locking, ACL checks, journals,
preimage authority, marker validation, rollback, and recovery cannot drift.
"""
from __future__ import annotations

from typing import Any

import project_os


def apply_managed_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Apply a trusted managed-surface plan with the canonical transaction."""
    return project_os.apply_init_plan(plan)
