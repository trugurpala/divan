from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import jwt
from jwt import PyJWKClient

from pusula.domain.identity import IdentityClaims, IdentityError, validate_verified_claims


class TokenVerificationError(ValueError):
    pass


@dataclass(frozen=True)
class LogtoJwtConfig:
    issuer: str
    audience: str
    jwks_url: str
    algorithms: tuple[str, ...] = ("RS256",)
    leeway_seconds: int = 30


class LogtoJwtVerifier:
    def __init__(self, config: LogtoJwtConfig, *, jwks_client: PyJWKClient | None = None) -> None:
        self._config = config
        self._jwks = jwks_client or PyJWKClient(config.jwks_url)

    def verify(
        self,
        token: str,
        *,
        required_scopes: Iterable[str] = (),
        expected_organization_id: str | None = None,
    ) -> IdentityClaims:
        if not token:
            raise TokenVerificationError("bearer token is required")
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self._config.algorithms),
                audience=self._config.audience,
                issuer=self._config.issuer,
                leeway=self._config.leeway_seconds,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
            return validate_verified_claims(
                claims,
                expected_issuer=self._config.issuer,
                expected_audience=self._config.audience,
                required_scopes=required_scopes,
                expected_organization_id=expected_organization_id,
            )
        except (jwt.PyJWTError, IdentityError, ValueError, TypeError) as exc:
            raise TokenVerificationError("invalid access token") from exc
