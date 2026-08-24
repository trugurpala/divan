from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from django.conf import settings
from django.http import HttpRequest

from pusula.auth.http_contract import AuthorizationHeaderError, extract_bearer_token
from pusula.auth.jwt_verifier import LogtoJwtConfig, LogtoJwtVerifier, TokenVerificationError
from pusula.domain.authorization import Action, Role
from pusula.domain.tenant import TenantAccessError, authorize_membership
from pusula.teams.service import get_membership_snapshot


class AuthConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RequestActor:
    subject: str
    team_id: uuid.UUID
    role: Role


@lru_cache(maxsize=1)
def _logto_verifier() -> LogtoJwtVerifier:
    issuer = str(getattr(settings, "LOGTO_ISSUER", "")).strip()
    audience = str(getattr(settings, "LOGTO_API_RESOURCE", "")).strip()
    jwks_url = str(getattr(settings, "LOGTO_JWKS_URL", "")).strip()
    if not issuer or not audience or not jwks_url:
        raise AuthConfigurationError("Logto issuer, audience and JWKS URL are required")
    return LogtoJwtVerifier(LogtoJwtConfig(issuer=issuer, audience=audience, jwks_url=jwks_url))


def authorize_request(
    request: HttpRequest,
    *,
    team_id: uuid.UUID,
    action: Action,
    required_scopes: Iterable[str] = (),
) -> RequestActor:
    try:
        token = extract_bearer_token(request.headers)
    except AuthorizationHeaderError as exc:
        raise TokenVerificationError("invalid access token") from exc

    claims = _logto_verifier().verify(token, required_scopes=required_scopes)
    membership = get_membership_snapshot(team_id=team_id, identity_subject=claims.subject)
    authorized = authorize_membership(
        membership,
        identity_subject=claims.subject,
        requested_team_id=str(team_id),
        action=action,
    )
    return RequestActor(subject=claims.subject, team_id=team_id, role=authorized.role)


__all__ = [
    "AuthConfigurationError",
    "RequestActor",
    "TenantAccessError",
    "TokenVerificationError",
    "authorize_request",
]
