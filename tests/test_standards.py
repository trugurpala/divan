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
SPEC = importlib.util.spec_from_file_location(
    "divan_standards", ROOT / "scripts" / "standards.py"
)
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
    def test_dcs_validation_does_not_require_project_registry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = {
                "schema_version": 1,
                "standards": [standard(number) for number in range(1, 12)],
            }
            write_fixture(root, data)
            self.assertEqual(STANDARTLAR.validate_contract(root), [])

    def test_project_standard_ids_and_applicability_are_exact(self) -> None:
        data = STANDARTLAR.load_project_contract(ROOT)
        self.assertEqual(
            [row["id"] for row in data["standards"]],
            [f"DPS-{number:03d}" for number in range(1, 13)],
        )
        applicable = {
            project_type
            for row in data["standards"]
            for project_type in row["applies_to"]
        }
        self.assertEqual(
            applicable,
            {
                "library",
                "service",
                "application",
                "public-web",
                "documentation",
                "monorepo",
            },
        )
        self.assertEqual(STANDARTLAR.validate_project_contract(ROOT), [])

    def test_project_waivers_reject_expired_long_and_invalid_records(self) -> None:
        waivers = {
            "schema_version": 1,
            "waivers": [
                {
                    "standard_id": "DPS-001",
                    "target": "README.md",
                    "reason": "migration",
                    "owner": "maintainer",
                    "created_on": "2026-01-01",
                    "expires_on": "2026-07-01",
                    "evidence": "README.md",
                },
                {
                    "standard_id": "DPS-999",
                    "target": "*.md",
                    "reason": "invalid",
                    "owner": "maintainer",
                    "created_on": "not-a-date",
                    "expires_on": "2027-01-01",
                    "evidence": "README.md",
                },
            ],
        }
        errors = STANDARTLAR.validate_waivers(waivers, today=STANDARTLAR.date(2026, 7, 23))
        self.assertTrue(any("expired" in error for error in errors))
        self.assertTrue(any("180" in error for error in errors))
        self.assertTrue(any("unknown" in error for error in errors))
        self.assertTrue(any("wildcard" in error for error in errors))
        self.assertTrue(any("YYYY-MM-DD" in error for error in errors))
        self.assertTrue(any("not declared" in error for error in errors))

    def test_malformed_project_type_registry_returns_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            (root / "registry").mkdir()
            (root / "registry" / "project-standards.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "waiver_max_days": 180,
                        "project_types": None,
                        "standards": [],
                    }
                ),
                encoding="utf-8",
            )
            errors = STANDARTLAR.validate_project_contract(root)
        self.assertIsInstance(errors, list)
        self.assertTrue(any("project_types" in error for error in errors))

    def test_each_dps_applicability_set_is_exact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            (root / "registry").mkdir()
            contract = STANDARTLAR.load_project_contract(ROOT)
            contract["standards"][10]["applies_to"] = ["library"]
            (root / "registry" / "project-standards.json").write_text(
                json.dumps(contract), encoding="utf-8"
            )
            errors = STANDARTLAR.validate_project_contract(root)
        self.assertTrue(
            any("DPS-011.applies_to" in error for error in errors)
        )

    def test_each_dps_evidence_target_set_is_exact(self) -> None:
        data = STANDARTLAR.load_project_contract(ROOT)
        self.assertEqual(
            {row["id"]: row["evidence"] for row in data["standards"]},
            {
                standard_id: list(targets)
                for standard_id, targets in (
                    STANDARTLAR.project_contracts.STANDARD_TARGETS.items()
                )
            },
        )
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            (root / "registry").mkdir()
            data["standards"][0]["evidence"] = [".divan/config.json"]
            (root / "registry" / "project-standards.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            errors = STANDARTLAR.validate_project_contract(root)
        self.assertTrue(
            any("DPS-001.evidence must match" in error for error in errors)
        )

    def test_required_ids_and_levels_are_exact(self) -> None:
        data = STANDARTLAR.load_contract(ROOT)
        self.assertEqual(STANDARTLAR.REQUIRED_IDS, tuple(f"DCS-{number:03d}" for number in range(1, 12)))
        self.assertEqual([row["id"] for row in data["standards"]], list(STANDARTLAR.REQUIRED_IDS))
        self.assertEqual({row["level"] for row in data["standards"]}, {"required"})

    def test_clean_code_and_lifecycle_standards_name_their_full_gates(self) -> None:
        rows = {row["id"]: row for row in STANDARTLAR.load_contract(ROOT)["standards"]}
        self.assertIn("python scripts/clean_code.py --check", rows["DCS-003"]["checks"])
        self.assertIn("scripts/clean_code.py", rows["DCS-003"]["evidence"])
        self.assertIn(
            "coverage run -m unittest discover -s tests",
            rows["DCS-005"]["checks"],
        )
        self.assertIn("coverage report --fail-under=64", rows["DCS-005"]["checks"])
        self.assertTrue(
            {"pyproject.toml", ".github/workflows/quality-gate.yml"}.issubset(
                rows["DCS-005"]["evidence"]
            )
        )
        lifecycle_tests = {
            "tests/test_host_upgrade.py",
            "tests/test_host_upgrade_security.py",
            "tests/test_host_upgrade_authority.py",
            "tests/test_host_upgrade_locking.py",
        }
        lifecycle_modules = {
            "scripts/host_upgrade.py",
            "scripts/host_transactions.py",
            "scripts/host_install_journal.py",
            "scripts/host_journal.py",
            "scripts/host_journal_scan.py",
            "scripts/host_journal_transitions.py",
            "scripts/host_state.py",
        }
        self.assertTrue(lifecycle_tests.issubset(rows["DCS-007"]["evidence"]))
        self.assertTrue(lifecycle_modules.issubset(rows["DCS-007"]["evidence"]))
        command = "python -m unittest " + " ".join(sorted(lifecycle_tests)) + " -v"
        self.assertIn(command, rows["DCS-007"]["checks"])

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

    def test_non_list_standards_returns_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            write_fixture(root, data)
            data["standards"] = None
            (root / "registry" / "community-standards.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            errors = STANDARTLAR.validate_contract(root)
        self.assertIsInstance(errors, list)
        self.assertTrue(any("community-standards.json.standards" in error for error in errors))

    def test_non_list_checks_returns_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            write_fixture(root, data)
            rows = data["standards"]
            assert isinstance(rows, list)
            rows[0]["checks"] = None
            (root / "registry" / "community-standards.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            errors = STANDARTLAR.validate_contract(root)
        self.assertIsInstance(errors, list)
        self.assertTrue(any("DCS-001.checks" in error for error in errors))

    def test_non_list_evidence_returns_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-standards-") as temporary:
            root = pathlib.Path(temporary)
            data = contract()
            write_fixture(root, data)
            rows = data["standards"]
            assert isinstance(rows, list)
            rows[0]["evidence"] = None
            (root / "registry" / "community-standards.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            errors = STANDARTLAR.validate_contract(root)
        self.assertIsInstance(errors, list)
        self.assertTrue(any("DCS-001.evidence" in error for error in errors))

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
