"""Validate and expose Divan's module and authority contracts."""
from __future__ import annotations

import pathlib
from typing import Any

from . import contract_validation

AUTHORITY_KEYS = {
    "id",
    "en",
    "tr",
    "rank",
    "receives_authority_from",
    "may_expand_scope",
}
RUNTIME_DATA_FILES = contract_validation.RUNTIME_DATA_FILES


def _validated_identity(value: object, field: str, identifier: str) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != {"id", "en", "tr"}
        or value.get("id") != identifier
    ):
        raise ValueError(f"{field} must use the canonical bilingual identity")
    return {
        "id": identifier,
        "en": contract_validation.label(value.get("en"), f"{field} en label"),
        "tr": contract_validation.label(value.get("tr"), f"{field} tr label"),
    }


def _validated_authority_row(
    value: object, index: int, expected_ids: list[str]
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != AUTHORITY_KEYS:
        raise ValueError("authority_chain rows must use the canonical schema")
    identifier = value["id"]
    rank = value["rank"]
    if (
        identifier != expected_ids[index]
        or type(rank) is not int
        or rank != index
        or not isinstance(value["may_expand_scope"], bool)
    ):
        raise ValueError("authority_chain order or identity is invalid")
    contract_validation.label(value.get("en"), f"authority {identifier} en label")
    contract_validation.label(value.get("tr"), f"authority {identifier} tr label")
    expected_source = None if index == 0 else expected_ids[index - 1]
    if value["receives_authority_from"] != expected_source:
        raise ValueError("authority_chain delegation is invalid")
    if value["may_expand_scope"] is not (identifier == "owner"):
        raise ValueError("only the owner may expand scope")
    return value


def _validated_authority(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("authority_chain must be a non-empty list")
    expected_ids = [
        "owner",
        "mandate",
        "orchestrator",
        "council",
        "specialist",
        "provider",
    ]
    if len(value) != len(expected_ids):
        raise ValueError("authority_chain must contain the canonical six levels")
    return [
        _validated_authority_row(row, index, expected_ids)
        for index, row in enumerate(value)
    ]


def _validate_governance(value: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "product",
        "governance_model",
        "authority_chain",
        "invariants",
    }
    if set(value) != expected:
        raise ValueError("governance.json must use the canonical schema")
    contract_validation.schema_version_one(
        value.get("schema_version"), "governance.json"
    )
    product = _validated_identity(value["product"], "product", "divan")
    governance_model = _validated_identity(
        value["governance_model"],
        "governance_model",
        "divan_governance_model",
    )
    authority = _validated_authority(value["authority_chain"])
    invariants = contract_validation.strings(
        value["invariants"], "governance invariants"
    )
    required_invariants = {
        "owner_is_final_authority",
        "delegation_cannot_expand_scope",
        "mutations_require_explicit_authority",
        "local_governance_uses_host_identity_boundary",
        "completion_requires_evidence",
        "core_has_no_external_runtime_dependency",
    }
    if not required_invariants.issubset(invariants):
        raise ValueError("governance invariants are incomplete")
    return {
        "product": product,
        "governance_model": governance_model,
        "authority_chain": authority,
        "invariants": invariants,
    }


def load_architecture(directory: pathlib.Path | None = None) -> dict[str, Any]:
    """Return a deterministic, validated view of the Divan runtime."""
    candidate = pathlib.Path(__file__).parent if directory is None else directory
    root = contract_validation.runtime_root(candidate)
    modules = contract_validation.load_modules(root)
    governance_path = contract_validation.runtime_file(root, "governance.json")
    governance = _validate_governance(contract_validation.load_json(governance_path))
    return {
        "authority_chain": governance["authority_chain"],
        "governance_model": governance["governance_model"],
        "invariants": governance["invariants"],
        "module_count": len(modules),
        "modules": modules,
        "product": governance["product"],
        "schema_version": 1,
        "status": "valid",
    }
