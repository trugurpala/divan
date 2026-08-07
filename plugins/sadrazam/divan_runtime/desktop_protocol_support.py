from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_API_VERSION = 1


class ProtocolValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def ok_response(result: Any) -> dict[str, Any]:
    return {"api_version": _API_VERSION, "ok": True, "result": result}


def error_response(code: str, message: str) -> dict[str, Any]:
    return {
        "api_version": _API_VERSION,
        "ok": False,
        "error": {"code": code, "message": message},
    }


def required_string(payload: Mapping[str, Any], key: str, code: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProtocolValidationError(code, f"{key} is required")
    return value.strip()


def optional_string(
    payload: Mapping[str, Any],
    key: str,
    code: str,
) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProtocolValidationError(code, f"{key} must be a string")
    value = value.strip()
    return value or None
