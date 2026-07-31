"""Privacy-bounded adoption receipts for the Divan Project Contract."""
from __future__ import annotations

import json
import pathlib
from typing import Any, cast

from . import adoption_common as common
from . import adoption_legacy as legacy
from . import adoption_schema2 as schema2

# Stable public constants retained for callers and compatibility tests.
JSON_MARKER_START = common.JSON_MARKER_START
JSON_MARKER_END = common.JSON_MARKER_END
SAFE_TOKEN = common.SAFE_TOKEN
SHA256 = common.SHA256
HOSTS = legacy.HOSTS
SUBMITTERS = legacy.SUBMITTERS
VERIFIED_STATES = legacy.VERIFIED_STATES
TEST_CLASSES = schema2.TEST_CLASSES


def _json_bytes(value: Any) -> bytes:
    return common.json_bytes(value)


def _digest(value: dict[str, Any]) -> str:
    return common.digest_schema_1(value)


def _digest_schema_2(value: dict[str, Any]) -> str:
    return common.digest_schema_2(value)


def _coarse_environment() -> dict[str, str]:
    return common.coarse_environment()


def _privacy_errors(value: Any, label: str = "receipt") -> list[str]:
    return common.privacy_errors(value, label)


def serialize_adoption_json(value: dict[str, object]) -> bytes:
    """Serialize one already verified adoption receipt."""
    return common.json_bytes(value)


def serialize_adoption_markdown(value: dict[str, object]) -> bytes:
    """Render a human-readable wrapper with the canonical JSON envelope."""
    if value.get("schema_version") == 1:
        return legacy.markdown(value)
    proof = value.get("proof")
    host = value.get("host")
    goal = value.get("goal")
    operator = value.get("operator")
    if not all(isinstance(item, dict) for item in (proof, host, goal, operator)):
        raise ValueError("schema 2 adoption receipt is incomplete")
    proof_value = cast(dict[str, Any], proof)
    host_value = cast(dict[str, Any], host)
    goal_value = cast(dict[str, Any], goal)
    operator_value = cast(dict[str, Any], operator)
    body = (
        "# Divan Clean-Room Adoption Receipt\n\n"
        f"- Status: `{goal_value['state']}`\n"
        f"- Host: `{host_value['name']} {host_value['version']}`\n"
        f"- Operator role: `{operator_value['role']}`\n"
        f"- Proof: `{proof_value['id']}`\n"
        f"- Receipt: `{proof_value['receipt_digest']}`\n\n"
        f"{JSON_MARKER_START}"
        f"{common.json_bytes(value).decode('utf-8')}"
        f"{JSON_MARKER_END}\n"
    )
    return body.encode("utf-8")


def export_adoption(
    project: pathlib.Path | str,
    goal_id: str,
    host: str,
    host_version: str,
    submitter: str = "maintainer",
) -> dict[str, Any]:
    """Build a legacy schema-1 declaration without writing files."""
    return legacy.export_adoption(project, goal_id, host, host_version, submitter)


def verify_adoption_value(
    value: dict[str, object], *, document_text: str | None = None
) -> dict[str, object]:
    """Verify one in-memory schema-1 or schema-2 adoption receipt."""
    if value.get("schema_version") == 1:
        result: dict[str, object] = legacy.verify_schema_1(value)
    elif value.get("schema_version") == 2:
        errors = schema2.errors(value) + common.privacy_errors(value)
        result = {
            "schema_version": 2,
            "status": "invalid" if errors else "valid-clean-room-adoption",
            "eligible_for_v1": not errors,
            "errors": sorted(set(errors)),
        }
    else:
        result = {
            "schema_version": value.get("schema_version", 0),
            "status": "invalid",
            "eligible_for_v1": False,
            "errors": ["adoption receipt schema is unsupported"],
        }
    if document_text is not None:
        document_errors = common.privacy_errors(document_text, "document")
        if document_errors:
            result["status"] = "invalid"
            result["eligible_for_v1"] = False
            result["errors"] = sorted(
                set(cast(list[str], result.get("errors", []))) | set(document_errors)
            )
    return result


def build_clean_room_receipt(
    *,
    divan: dict[str, object],
    host: dict[str, object],
    environment: dict[str, object],
    operator: dict[str, object],
    project: dict[str, object],
    goal: dict[str, object],
    checks: list[dict[str, object]],
    proof: dict[str, object],
) -> dict[str, object]:
    """Build and verify one canonical schema-2 clean-room receipt."""
    return schema2.build(
        divan=divan,
        host=host,
        environment=environment,
        operator=operator,
        project=project,
        goal=goal,
        checks=checks,
        proof=proof,
    )


def verify_adoption(path: pathlib.Path | str) -> dict[str, Any]:
    """Verify receipt schema, digest, privacy, and technical eligibility."""
    receipt_path = pathlib.Path(path)
    try:
        value, document = common.read_receipt(receipt_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {
            "schema_version": 0,
            "status": "invalid",
            "eligible_for_v1": False,
            "errors": [str(error)],
        }
    result = verify_adoption_value(value, document_text=document)
    if (
        receipt_path.suffix.casefold() == ".md"
        and value.get("schema_version") == 2
        and result.get("status") == "valid-clean-room-adoption"
        and document != serialize_adoption_markdown(value).decode("utf-8")
    ):
        result["status"] = "invalid"
        result["eligible_for_v1"] = False
        result["errors"] = sorted(
            set(cast(list[str], result.get("errors", [])))
            | {"Markdown adoption receipt is not canonical"}
        )
    return result
