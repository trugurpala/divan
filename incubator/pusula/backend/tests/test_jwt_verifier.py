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
    def __init__(self, public_key: rsa.RSAPublicKey) -> None:
        numbers = public_key.public_numbers()
        jwk = {
            "kty": "RSA",
            "kid": "test-key",
            "use": "sig",
            "alg": "RS256",
            "n": _b64u(numbers.n),
            "e": _b64u(numbers.e),
        }
        self._key = PyJWK.from_json(json.dumps(jwk))

    def get_signing_key_from_jwt(self, token: str) -> PyJWK:
        if jwt.get_unverified_header(token).get("kid") != "test-key":
            raise jwt.PyJWKClientError("unknown kid")
        return self._key


class JwtVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.config = LogtoJwtConfig(
            issuer="https://id.pusula.test/oidc",
            audience="https://api.pusula.test",
            jwks_url="https://id.pusula.test/oidc/jwks",
            leeway_seconds=0,
        )
        cls.verifier = LogtoJwtVerifier(
            cls.config,
            jwks_client=StubJwksClient(cls.private_key.public_key()),
        )

    def issue(self, **overrides: object) -> str:
        now = dt.datetime.now(dt.timezone.utc)
        payload: dict[str, object] = {
            "iss": self.config.issuer,
            "sub": "user-1",
            "aud": self.config.audience,
            "iat": now,
            "exp": now + dt.timedelta(minutes=5),
            "scope": "projects:read goals:write",
        }
        payload.update(overrides)
        return jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )

    def test_accepts_valid_token(self) -> None:
        claims = self.verifier.verify(self.issue(), required_scopes={"projects:read"})
        self.assertEqual(claims.subject, "user-1")

    def test_enforces_organization_context(self) -> None:
        token = self.issue(organization_id="team-a")
        self.assertEqual(
            self.verifier.verify(token, expected_organization_id="team-a").organization_id,
            "team-a",
        )
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(token, expected_organization_id="team-b")

    def test_rejects_algorithm_downgrade(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        token = jwt.encode(
            {"iss": self.config.issuer, "sub": "u", "aud": self.config.audience, "iat": now, "exp": now + dt.timedelta(minutes=5)},
            "x" * 32,
            algorithm="HS256",
            headers={"kid": "test-key"},
        )
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(token)

    def test_rejects_expired(self) -> None:
        expired = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(self.issue(exp=expired))

    def test_rejects_missing_scope(self) -> None:
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(self.issue(), required_scopes={"admin"})

    def test_rejects_unknown_kid(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        token = jwt.encode(
            {"iss": self.config.issuer, "sub": "u", "aud": self.config.audience, "iat": now, "exp": now + dt.timedelta(minutes=5)},
            self.private_key,
            algorithm="RS256",
            headers={"kid": "unknown"},
        )
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(token)

    def test_rejects_wrong_audience(self) -> None:
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(self.issue(aud="https://other.test"))

    def test_rejects_wrong_issuer(self) -> None:
        with self.assertRaises(TokenVerificationError):
            self.verifier.verify(self.issue(iss="https://evil.test"))


if __name__ == "__main__":
    unittest.main()
