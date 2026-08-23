from __future__ import annotations

import datetime as dt
import json
import unittest
from base64 import urlsafe_b64encode

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from pusula.auth.jwt_verifier import LogtoJwtConfig, LogtoJwtVerifier, TokenVerificationError


def _b64u(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class StubJwksClient:
    def __init__(self, jwk: PyJWK) -> None:
        self._jwk = jwk

    def get_signing_key_from_jwt(self, token: str) -> PyJWK:
        header = jwt.get_unverified_header(token)
        if header.get("kid") != self._jwk.key_id:
            raise jwt.PyJWKClientError("unknown kid")
        return self._jwk


class JwtVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_numbers = private_key.public_key().public_numbers()
        jwk_data = {
            "kty": "RSA",
            "kid": "test-key",
            "use": "sig",
            "alg": "RS256",
            "n": _b64u(public_numbers.n),
            "e": _b64u(public_numbers.e),
        }
        cls.private_key = private_key
        cls.jwk = PyJWK.from_json(json.dumps(jwk_data))
        cls.config = LogtoJwtConfig(
            issuer="https://id.pusula.test/oidc",
            audience="https://api.pusula.test",
            jwks_url="https://id.pusula.test/oidc/jwks",
            leeway_seconds=0,
        )

    def _token(self, **overrides: object) -> str:
        now = dt.datetime.now(tz=dt.UTC)
        claims: dict[str, object] = {
            "sub": "user-1",
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "iat": now,
            "exp": now + dt.timedelta(minutes=5),
            "scope": "projects:read goals:write",
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private_key, algorithm="RS256", headers={"kid": "test-key"})

    def _verifier(self) -> LogtoJwtVerifier:
        return LogtoJwtVerifier(self.config, jwks_client=StubJwksClient(self.jwk))

    def test_accepts_valid_signed_token(self) -> None:
        claims = self._verifier().verify(self._token(), required_scopes={"projects:read"})
        self.assertEqual(claims.subject, "user-1")

    def test_rejects_wrong_issuer(self) -> None:
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(self._token(iss="https://evil.test"))

    def test_rejects_wrong_audience(self) -> None:
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(self._token(aud="https://wrong.test"))

    def test_rejects_expired_token(self) -> None:
        expired = dt.datetime.now(tz=dt.UTC) - dt.timedelta(minutes=1)
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(self._token(exp=expired))

    def test_rejects_missing_scope(self) -> None:
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(self._token(), required_scopes={"admin"})

    def test_checks_organization_context(self) -> None:
        claims = self._verifier().verify(
            self._token(organization_id="org-a"),
            expected_organization_id="org-a",
        )
        self.assertEqual(claims.organization_id, "org-a")

    def test_rejects_wrong_organization_context(self) -> None:
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(
                self._token(organization_id="org-b"),
                expected_organization_id="org-a",
            )

    def test_rejects_wrong_kid(self) -> None:
        token = jwt.encode(
            {
                "sub": "user-1",
                "iss": self.config.issuer,
                "aud": self.config.audience,
                "iat": dt.datetime.now(tz=dt.UTC),
                "exp": dt.datetime.now(tz=dt.UTC) + dt.timedelta(minutes=5),
            },
            self.private_key,
            algorithm="RS256",
            headers={"kid": "unknown"},
        )
        with self.assertRaisesRegex(TokenVerificationError, "invalid access token"):
            self._verifier().verify(token)


if __name__ == "__main__":
    unittest.main()
