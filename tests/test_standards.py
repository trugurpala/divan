from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_standartlar", ROOT / "scripts" / "standartlar.py")
assert SPEC and SPEC.loader
STANDARTLAR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STANDARTLAR)


def standard(number: int) -> dict[str, object]:
    return {
        "id": f"DCS-{number:03d}",
        "title_tr": f"Turkce baslik {number}",
        "title_en": f"English title {number}",
        "level": "required",
        "purpose": f"Purpose {number}",
        "checks": ["python scripts/validate.py"],
        "evidence": ["README.md"],
        "exception_policy": "Narrow, documented, and expiring exceptions only.",
    }


def contract() -> dict[str, object]:
    return {"schema_version": 1, "standards": [standard(number) for number in range(1, 11)]}


def write_fixture(root: pathlib.Path, data: dict[str, object], exceptions: object = None) -> None:
    (root / "registry").mkdir()
    (root / "docs").mkdir()
    (root / "README.md").write_text("evidence\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "validate.py").write_text("", encoding="utf-8")
    (root / "registry" / "community-standards.json").write_text(
        json.dumps(data), encoding="utf-8"
    )
    (root / "registry" / "standard-exceptions.json").write_text(
        json.dumps([] if exceptions is None else exceptions), encoding="utf-8"
    )
    (root / "docs" / "Topluluk-Standartlari.md").write_text(
        STANDARTLAR.render_markdown(data), encoding="utf-8"
    )


class CommunityStandardsTests(unittest.TestCase):
    def test_required_ids_and_levels_are_exact(self) -> None:
        data = STANDARTLAR.load_contract(ROOT)
        self.assertEqual(STANDARTLAR.REQUIRED_IDS, tuple(f"DCS-{number:03d}" for number in range(1, 11)))
        self.assertEqual([row["id"] for row in data["standards"]], list(STANDARTLAR.REQUIRED_IDS))
        self.assertEqual({row["level"] for row in data["standards"]}, {"required"})

    def test_duplicate_and_missing_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            rows = data["standards"]
            assert isinstance(rows, list)
            rows[-1] = standard(9)
            write_fixture(root, data)
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("DCS-009 tekrarli" in error for error in errors))
        self.assertTrue(any("DCS-010 eksik" in error for error in errors))

    def test_missing_check_and_evidence_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            rows = data["standards"]
            assert isinstance(rows, list)
            rows[0]["checks"] = []
            rows[1]["evidence"] = []
            write_fixture(root, data)
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("DCS-001.checks" in error for error in errors))
        self.assertTrue(any("DCS-002.evidence" in error for error in errors))

    def test_check_referencing_a_missing_script_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            rows = data["standards"]
            assert isinstance(rows, list)
            rows[0]["checks"] = ["python scripts/missing.py --check"]
            write_fixture(root, data)
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("DCS-001.checks bulunamadi" in error for error in errors))

    def test_expired_and_duplicate_exceptions_are_rejected(self) -> None:
        exceptions = [
            {
                "standard_id": "DCS-001",
                "target": "README.md",
                "reason": "Temporary migration",
                "owner": "maintainer",
                "created_on": "2026-01-01",
                "expires_on": "2026-01-02",
                "evidence": "README.md",
            },
            {
                "standard_id": "DCS-001",
                "target": "README.md",
                "reason": "Duplicate target",
                "owner": "maintainer",
                "created_on": "2026-07-01",
                "expires_on": "2026-07-31",
                "evidence": "README.md",
            },
        ]
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            write_fixture(root, contract(), exceptions)
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("suresi dolmus" in error for error in errors))
        self.assertTrue(any("tekrarli istisna" in error for error in errors))

    def test_exception_expiry_is_limited_and_wildcards_are_rejected(self) -> None:
        exception = {
            "standard_id": "DCS-001",
            "target": "docs/*.md",
            "reason": "Temporary migration",
            "owner": "maintainer",
            "created_on": "2026-01-01",
            "expires_on": "2026-07-01",
            "evidence": "README.md",
        }
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            write_fixture(root, contract(), [exception])
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("180 gunden uzun" in error for error in errors))
        self.assertTrue(any("joker hedef" in error for error in errors))

    def test_rendering_is_deterministic(self) -> None:
        data = contract()
        first = STANDARTLAR.render_markdown(data)
        self.assertEqual(first, STANDARTLAR.render_markdown(json.loads(json.dumps(data))))
        self.assertTrue(first.endswith("\n"))
        self.assertIn("DCS-001", first)
        self.assertIn("DCS-010", first)

    def test_stale_document_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            write_fixture(root, contract())
            (root / "docs" / "Topluluk-Standartlari.md").write_text("stale\n", encoding="utf-8")
            errors = STANDARTLAR.validate_contract(root)
        self.assertTrue(any("uretilmis belge eski" in error for error in errors))

    def test_json_mode_writes_only_a_json_status_object(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(STANDARTLAR, "validate_contract", return_value=[]):
            result = STANDARTLAR.main(["--json"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue()), {"errors": [], "ok": True})


if __name__ == "__main__":
    unittest.main()
