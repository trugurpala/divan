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


if __name__ == "__main__":
    unittest.main()
