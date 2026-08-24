from __future__ import annotations

from typing import Mapping


class AuthorizationHeaderError(ValueError):
    pass


def extract_bearer_token(headers: Mapping[str, str]) -> str:
    value = headers.get("Authorization") or headers.get("authorization")
    if value is None:
        raise AuthorizationHeaderError("authorization header is required")
    parts = value.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AuthorizationHeaderError("authorization header must use Bearer token")
    return parts[1]
