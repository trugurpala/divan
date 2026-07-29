"""Public helpers for Divan's Hükümdar-first local governance contract."""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

from . import kernel

__all__ = [
    "architecture",
    "authority_chain",
    "authorize_mutation",
    "may_expand_scope",
]


def architecture(directory: pathlib.Path | None = None) -> dict[str, Any]:
    """Return the complete validated runtime architecture."""
    return kernel.load_architecture(directory)


def authority_chain(directory: pathlib.Path | None = None) -> list[dict[str, Any]]:
    """Return the ordered, bilingual delegation chain."""
    return list(architecture(directory)["authority_chain"])


def may_expand_scope(actor_id: str, directory: pathlib.Path | None = None) -> bool:
    """Return whether an actor may expand the mandate's scope."""
    return any(
        row["id"] == actor_id and row["may_expand_scope"]
        for row in authority_chain(directory)
    )


def authorize_mutation(
    actor_id: str,
    operation: str,
    scope: dict[str, Any],
    *,
    explicit_authority: bool,
    directory: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Bind one public CLI mutation to explicit owner authority and exact scope.

    This is a local process boundary, not user authentication. The host
    operating-system account remains the identity and permission boundary.
    """
    actors = {str(row["id"]): row for row in authority_chain(directory)}
    if actor_id not in actors:
        raise ValueError(f"unknown Divan authority actor: {actor_id}")
    if not explicit_authority:
        raise ValueError("mutation requires the explicit --execute authority flag")
    if not may_expand_scope(actor_id, directory):
        raise ValueError("only owner/Hükümdar may authorize a public CLI mutation")
    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("mutation operation must be non-empty")
    canonical_scope = json.dumps(
        scope,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    mandate_id = "mandate-" + hashlib.sha256(
        f"{operation.strip()}\n{canonical_scope}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "actor_id": actor_id,
        "authority_source": "explicit_execute_flag",
        "identity_boundary": "host_os_account",
        "mandate_id": mandate_id,
        "operation": operation.strip(),
        "scope": json.loads(canonical_scope),
    }
