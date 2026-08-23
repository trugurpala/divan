from __future__ import annotations

import unittest

from pusula.auth.http_contract import AuthorizationHeaderError, extract_bearer_token


class AuthorizationHeaderTests(unittest.TestCase):
    def test_extracts_bearer_token(self) -> None:
        self.assertEqual(extract_bearer_token({"Authorization": "Bearer abc"}), "abc")

    def test_scheme_is_case_insensitive(self) -> None:
        self.assertEqual(extract_bearer_token({"authorization": "bearer abc"}), "abc")

    def test_rejects_missing_header(self) -> None:
        with self.assertRaisesRegex(AuthorizationHeaderError, "required"):
            extract_bearer_token({})

    def test_rejects_wrong_scheme(self) -> None:
        with self.assertRaisesRegex(AuthorizationHeaderError, "Bearer"):
            extract_bearer_token({"Authorization": "Basic abc"})

    def test_rejects_extra_parts(self) -> None:
        with self.assertRaisesRegex(AuthorizationHeaderError, "Bearer"):
            extract_bearer_token({"Authorization": "Bearer abc def"})


if __name__ == "__main__":
    unittest.main()
