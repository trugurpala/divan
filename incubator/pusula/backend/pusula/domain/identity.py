from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class IdentityError(ValueError):
    pass


@dataclass(frozen=True)
class IdentityClaims:
    subject: str
    issuer: str
    audiences: frozenset[str]
    scopes: frozenset[str]
    organization_id: str | None


def _as_audiences(value: object) -> frozenset[str]:
    if isinstance(value, str) and value:
        return frozenset({value})
    if isinstance(value, list) and all(isinstance(item, str) and item for item in value):
        return frozenset(value)
    raise IdentityError("aud claim must be a non-empty string or string list")


def _as_scopes(value: object) -> frozenset[str]:
    if value is None:
        return frozenset()
    if not isinstance(value, str):
        raise IdentityError("scope claim must be a string")
    return frozenset(part for part in value.split() if part)


def validate_verified_claims(
    claims: Mapping[str, Any],
    *,
    expected_issuer: str,
    expected_audience: str,
    required_scopes: Iterable[str] = (),
    expected_organization_id: str | None = None,
) -> IdentityClaims:
    """Validate semantic claims after JWT signature and expiration verification."""
    subject = claims.get("sub")
    issuer = claims.get("iss")
    if not isinstance(subject, str) or not subject:
        raise IdentityError("sub claim is required")
    if issuer != expected_issuer:
        raise IdentityError("issuer mismatch")

    audiences = _as_audiences(claims.get("aud"))
    if expected_audience not in audiences:
        raise IdentityError("audience mismatch")

    scopes = _as_scopes(claims.get("scope"))
    missing = frozenset(required_scopes) - scopes
    if missing:
        raise IdentityError("required scope missing")

    organization = claims.get("organization_id")
    if organization is not None and not isinstance(organization, str):
        raise IdentityError("organization_id must be a string")
    if expected_organization_id is not None and organization != expected_organization_id:
        raise IdentityError("organization context mismatch")

    return IdentityClaims(
        subject=subject,
        issuer=issuer,
        audiences=audiences,
        scopes=scopes,
        organization_id=organization,
    )
