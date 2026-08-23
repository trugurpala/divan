from __future__ import annotations

import unittest

from pusula.domain.identity import IdentityError, validate_verified_claims

BASE = {
    "sub": "user-1",
    "iss": "https://id.pusula.test/oidc",
    "aud": "https://api.pusula.test",
    "scope": "projects:read goals:write",
}


class IdentityTests(unittest.TestCase):
    def test_accepts_valid_claims(self) -> None:
        result = validate_verified_claims(
            BASE,
            expected_issuer=BASE["iss"],
            expected_audience=BASE["aud"],
            required_scopes={"projects:read"},
        )
        self.assertEqual(result.subject, "user-1")

    def test_accepts_audience_list(self) -> None:
        claims = {**BASE, "aud": ["other", BASE["aud"]]}
        result = validate_verified_claims(
            claims,
            expected_issuer=BASE["iss"],
            expected_audience=BASE["aud"],
        )
        self.assertIn(BASE["aud"], result.audiences)

    def test_rejects_wrong_issuer(self) -> None:
        with self.assertRaisesRegex(IdentityError, "issuer mismatch"):
            validate_verified_claims(
                BASE,
                expected_issuer="https://evil",
                expected_audience=BASE["aud"],
            )

    def test_rejects_wrong_audience(self) -> None:
        with self.assertRaisesRegex(IdentityError, "audience mismatch"):
            validate_verified_claims(
                BASE,
                expected_issuer=BASE["iss"],
                expected_audience="https://wrong",
            )

    def test_rejects_missing_subject(self) -> None:
        claims = {key: value for key, value in BASE.items() if key != "sub"}
        with self.assertRaisesRegex(IdentityError, "sub claim"):
            validate_verified_claims(claims, expected_issuer=BASE["iss"], expected_audience=BASE["aud"])

    def test_rejects_missing_scope(self) -> None:
        with self.assertRaisesRegex(IdentityError, "required scope"):
            validate_verified_claims(
                BASE,
                expected_issuer=BASE["iss"],
                expected_audience=BASE["aud"],
                required_scopes={"admin"},
            )

    def test_accepts_expected_org(self) -> None:
        claims = {**BASE, "organization_id": "team-a"}
        result = validate_verified_claims(
            claims,
            expected_issuer=BASE["iss"],
            expected_audience=BASE["aud"],
            expected_organization_id="team-a",
        )
        self.assertEqual(result.organization_id, "team-a")

    def test_rejects_wrong_org(self) -> None:
        claims = {**BASE, "organization_id": "team-b"}
        with self.assertRaisesRegex(IdentityError, "organization context"):
            validate_verified_claims(
                claims,
                expected_issuer=BASE["iss"],
                expected_audience=BASE["aud"],
                expected_organization_id="team-a",
            )

    def test_rejects_malformed_audience(self) -> None:
        with self.assertRaisesRegex(IdentityError, "aud claim"):
            validate_verified_claims(
                {**BASE, "aud": 5},
                expected_issuer=BASE["iss"],
                expected_audience=BASE["aud"],
            )

    def test_rejects_malformed_scope(self) -> None:
        with self.assertRaisesRegex(IdentityError, "scope claim"):
            validate_verified_claims(
                {**BASE, "scope": ["read"]},
                expected_issuer=BASE["iss"],
                expected_audience=BASE["aud"],
            )
