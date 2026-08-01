from __future__ import annotations

import copy
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import host_compatibility

ROOT = pathlib.Path(__file__).resolve().parents[1]


class HostCompatibilityTests(unittest.TestCase):
    def test_repository_registry_is_valid_and_complete(self) -> None:
        self.assertEqual(host_compatibility.validate(ROOT), [])
        data = host_compatibility.load(ROOT)
        self.assertEqual(
            [row["id"] for row in data["hosts"]],
            list(host_compatibility.HOST_IDS),
        )

    def test_verified_claim_requires_real_evidence(self) -> None:
        data = copy.deepcopy(host_compatibility.load(ROOT))
        cursor = next(row for row in data["hosts"] if row["id"] == "cursor")
        cursor["tier"] = "verified"
        cursor["evidence"] = []
        with tempfile.TemporaryDirectory(prefix="divan-hosts-") as temporary:
            root = pathlib.Path(temporary)
            (root / "registry").mkdir()
            (root / "registry" / "host-compatibility.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            errors = host_compatibility.validate(root)
        self.assertTrue(any("evidence is required" in error for error in errors))

    def test_unknown_capability_and_tier_regression_are_rejected(self) -> None:
        data = copy.deepcopy(host_compatibility.load(ROOT))
        data["hosts"][0]["capabilities"].append("magic")
        data["hosts"][0]["target_tier"] = "experimental"
        with mock.patch.object(host_compatibility, "load", return_value=data):
            errors = host_compatibility.validate(ROOT)
        self.assertTrue(any("unknown values" in error for error in errors))
        self.assertTrue(any("cannot be lower" in error for error in errors))

    def test_every_host_declares_non_empty_supported_surfaces(self) -> None:
        data = copy.deepcopy(host_compatibility.load(ROOT))
        data["hosts"][0].pop("surfaces", None)
        with mock.patch.object(host_compatibility, "load", return_value=data):
            errors = host_compatibility.validate(ROOT)
        self.assertTrue(any("surfaces must be a non-empty list" in error for error in errors))

    def test_codex_verified_claim_is_limited_to_repository_evidence(self) -> None:
        data = host_compatibility.load(ROOT)
        codex = next(row for row in data["hosts"] if row["id"] == "codex")
        self.assertEqual(codex["surfaces"], ["cli"])
        self.assertEqual(
            codex["excluded_surfaces"],
            ["desktop", "ide-extension", "mobile"],
        )

    def test_surface_claims_reject_duplicates_malformed_and_overlap(self) -> None:
        data = copy.deepcopy(host_compatibility.load(ROOT))
        codex = next(row for row in data["hosts"] if row["id"] == "codex")
        codex["surfaces"] = ["desktop", "desktop", "IDE Extension"]
        codex["excluded_surfaces"] = ["desktop"]
        with mock.patch.object(host_compatibility, "load", return_value=data):
            errors = host_compatibility.validate(ROOT)
        self.assertTrue(any("surfaces contains duplicates" in error for error in errors))
        self.assertTrue(any("surfaces contains malformed values" in error for error in errors))
        self.assertTrue(any("surface claims overlap" in error for error in errors))

    def test_unhashable_registry_values_are_reported_instead_of_crashing(self) -> None:
        data = copy.deepcopy(host_compatibility.load(ROOT))
        data["hosts"][0]["id"] = ["not", "a", "string"]
        data["hosts"][0]["surfaces"] = [["not-a-surface"]]
        data["hosts"][0]["excluded_surfaces"] = [{"not": "a-surface"}]
        with mock.patch.object(host_compatibility, "load", return_value=data):
            errors = host_compatibility.validate(ROOT)
        self.assertTrue(any("id must be kebab-case ASCII" in error for error in errors))
        self.assertTrue(any("surfaces contains malformed values" in error for error in errors))
        self.assertTrue(any("excluded_surfaces contains malformed values" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
