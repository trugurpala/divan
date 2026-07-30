from __future__ import annotations

import copy
import importlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
if str(COMPANY) not in sys.path:
    sys.path.insert(0, str(COMPANY))

adoption = importlib.import_module("adoption")

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64
HASH_E = "sha256:" + "e" * 64
HASH_F = "sha256:" + "f" * 64


def clean_room_parts(role: str = "maintainer") -> dict[str, object]:
    return {
        "divan": {
            "version": "0.18.3",
            "ref": "v0.18.3",
            "commit": "a" * 40,
            "distribution": "immutable-release",
            "runner_sha256": HASH_A,
        },
        "host": {
            "name": "claude-code",
            "version": "2.1.220",
            "version_source": "observed-cli",
        },
        "environment": {"os": "windows", "architecture": "x86_64"},
        "operator": {"role": role},
        "project": {
            "identity_sha256": HASH_B,
            "distinct_from_divan": True,
            "distinctness_policy_sha256": HASH_C,
            "types": ["application", "monorepo"],
            "workspace_count": 11,
        },
        "goal": {
            "id": "goal-5e033a4d324a",
            "state": "VERIFIED",
            "target": "VERIFIED",
            "receipt_sha256": HASH_D,
            "artifact_sha256": [HASH_E],
        },
        "checks": [
            {
                "id": "root:test",
                "class": "test",
                "workspace_sha256": HASH_B,
                "runner": "bun",
                "name": "test",
                "argv_sha256": HASH_C,
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 18500,
                "timeout_ms": 120000,
                "timeout_policy_sha256": HASH_D,
                "output_sha256": HASH_F,
            }
        ],
        "proof": {
            "id": "proof-123456789abc",
            "started_at": "2026-07-30T10:00:00Z",
            "completed_at": "2026-07-30T10:00:19Z",
            "source_stable": True,
        },
    }


class CleanRoomAdoptionReceiptTests(unittest.TestCase):
    def test_builds_valid_schema_2_for_both_operator_roles(self) -> None:
        for role in ("maintainer", "external"):
            with self.subTest(role=role):
                value = adoption.build_clean_room_receipt(
                    **clean_room_parts(role)
                )
                verification = adoption.verify_adoption_value(value)
                self.assertEqual(
                    verification,
                    {
                        "schema_version": 2,
                        "status": "valid-clean-room-adoption",
                        "eligible_for_v1": True,
                        "errors": [],
                    },
                )
                self.assertEqual(value["operator"]["role"], role)

    def test_json_and_markdown_have_identical_offline_meaning(self) -> None:
        value = adoption.build_clean_room_receipt(**clean_room_parts())
        with tempfile.TemporaryDirectory(
            prefix="divan-clean-room-"
        ) as temporary:
            root = pathlib.Path(temporary)
            json_path = root / "adoption-receipt.json"
            markdown_path = root / "adoption-receipt.md"
            json_path.write_bytes(adoption.serialize_adoption_json(value))
            markdown_path.write_bytes(
                adoption.serialize_adoption_markdown(value)
            )

            json_result = adoption.verify_adoption(json_path)
            markdown_result = adoption.verify_adoption(markdown_path)

        self.assertEqual(json_result, markdown_result)
        self.assertEqual(
            json_result["status"], "valid-clean-room-adoption"
        )

    def test_rejects_empty_or_build_only_checks(self) -> None:
        empty = clean_room_parts()
        empty["checks"] = []
        with self.assertRaisesRegex(ValueError, "checks"):
            adoption.build_clean_room_receipt(**empty)

        build_only = clean_room_parts()
        build_only["checks"][0]["id"] = "root:build"
        build_only["checks"][0]["class"] = "build"
        build_only["checks"][0]["name"] = "build"
        with self.assertRaisesRegex(ValueError, "test-class"):
            adoption.build_clean_room_receipt(**build_only)

    def test_rejects_tamper_even_when_digest_is_recomputed(self) -> None:
        value = adoption.build_clean_room_receipt(**clean_room_parts())
        value["checks"][0]["exit_code"] = 9
        value["proof"]["receipt_digest"] = adoption._digest_schema_2(value)

        result = adoption.verify_adoption_value(value)

        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["eligible_for_v1"])
        self.assertTrue(
            any("passed check" in error for error in result["errors"])
        )

    def test_rejects_unknown_keys_bad_order_and_boolean_integers(self) -> None:
        cases: list[dict[str, object]] = []
        unknown = clean_room_parts()
        unknown["host"]["claim"] = "trusted"
        cases.append(unknown)

        order = clean_room_parts()
        second = copy.deepcopy(order["checks"][0])
        second["id"] = "aaa:test"
        second["workspace_sha256"] = HASH_E
        order["checks"].append(second)
        cases.append(order)

        boolean = clean_room_parts()
        boolean["checks"][0]["duration_ms"] = True
        cases.append(boolean)

        for parts in cases:
            with self.subTest(parts=parts):
                with self.assertRaises(ValueError):
                    adoption.build_clean_room_receipt(**parts)

    def test_rejects_privacy_leaks_in_json_and_markdown(self) -> None:
        parts = clean_room_parts()
        parts["host"]["version"] = "mail@example.com"
        with self.assertRaisesRegex(ValueError, "email"):
            adoption.build_clean_room_receipt(**parts)

        value = adoption.build_clean_room_receipt(**clean_room_parts())
        document = (
            adoption.serialize_adoption_markdown(value).decode("utf-8")
            + "\npassword=not-public\n"
        )
        result = adoption.verify_adoption_value(
            json.loads(
                document.split(adoption.JSON_MARKER_START, 1)[1].split(
                    adoption.JSON_MARKER_END, 1
                )[0]
            ),
            document_text=document,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["errors"])

    def test_markdown_visible_summary_must_match_embedded_json(self) -> None:
        value = adoption.build_clean_room_receipt(**clean_room_parts())
        with tempfile.TemporaryDirectory(
            prefix="divan-adoption-markdown-"
        ) as temporary:
            path = pathlib.Path(temporary) / "receipt.md"
            document = adoption.serialize_adoption_markdown(value).decode(
                "utf-8"
            )
            path.write_text(
                document.replace("claude-code 2.1.220", "codex 99.99"),
                encoding="utf-8",
            )

            result = adoption.verify_adoption(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("canonical", " ".join(result["errors"]))

    def test_rejects_false_distinctness_unobserved_host_and_source_drift(
        self,
    ) -> None:
        cases = []
        not_distinct = clean_room_parts()
        not_distinct["project"]["distinct_from_divan"] = False
        cases.append(not_distinct)
        unobserved = clean_room_parts()
        unobserved["host"]["version_source"] = "caller"
        cases.append(unobserved)
        drifted = clean_room_parts()
        drifted["proof"]["source_stable"] = False
        cases.append(drifted)

        for parts in cases:
            with self.subTest(parts=parts):
                with self.assertRaises(ValueError):
                    adoption.build_clean_room_receipt(**parts)


if __name__ == "__main__":
    unittest.main()
