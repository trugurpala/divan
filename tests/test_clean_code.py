from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import tomllib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_clean_code", ROOT / "scripts" / "clean_code.py"
)
assert SPEC and SPEC.loader
CLEAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLEAN)


def ruff_result(findings: list[dict[str, object]]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        ["ruff"],
        1 if findings else 0,
        stdout=json.dumps(findings),
        stderr="",
    )


class CleanCodeTests(unittest.TestCase):
    def test_quality_gate_and_release_manifest_include_clean_code_contracts(self) -> None:
        configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(configuration["tool"]["coverage"]["report"]["fail_under"], 64)
        self.assertEqual(
            configuration["tool"]["mypy"]["files"],
            ["scripts", "evals", "plugins/sadrazam/company"],
        )
        self.assertEqual(
            configuration["tool"]["coverage"]["run"]["source"],
            ["scripts", "evals", "plugins/sadrazam/company"],
        )
        self.assertEqual(
            configuration["tool"]["ruff"]["extend-exclude"],
            ["plugins/*/skills"],
        )

        workflow = (ROOT / ".github" / "workflows" / "quality-gate.yml").read_text(
            encoding="utf-8"
        )
        self.assertLess(workflow.index("ruff check ."), workflow.index("clean_code.py --check"))
        self.assertLess(
            workflow.index("clean_code.py --check"),
            workflow.index("mypy scripts evals plugins/sadrazam/company"),
        )
        self.assertIn("coverage report --fail-under=64", workflow)

        manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
        paths = {surface["path"] for surface in manifest["public_surfaces"]}
        self.assertTrue(
            {
                "registry/clean-code-baseline.json",
                "scripts/clean_code.py",
                "evals/provenance.py",
                "evals/result_contracts.py",
            }.issubset(paths)
        )

    def test_new_401_line_module_is_measured(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-clean-code-") as temporary:
            root = pathlib.Path(temporary)
            path = root / "scripts" / "oversized.py"
            path.parent.mkdir()
            path.write_text("# fixture\n" * 401, encoding="utf-8")
            with mock.patch.object(CLEAN.subprocess, "run", return_value=ruff_result([])):
                measured = CLEAN.measure_python(root)

        self.assertEqual(measured["module-lines"], {"scripts/oversized.py": 401})

    def test_new_51_logical_line_function_is_measured_by_exact_symbol(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-clean-code-") as temporary:
            root = pathlib.Path(temporary)
            path = root / "evals" / "long_function.py"
            path.parent.mkdir()
            body = "".join(f"    value_{index} = {index}\n" for index in range(50))
            path.write_text("def long_function():\n" + body, encoding="utf-8")
            with mock.patch.object(CLEAN.subprocess, "run", return_value=ruff_result([])):
                measured = CLEAN.measure_python(root)

        self.assertEqual(
            measured["function-lines"],
            {"evals/long_function.py:long_function": 51},
        )

    def test_new_ruff_complexity_11_is_measured_by_exact_symbol(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-clean-code-") as temporary:
            root = pathlib.Path(temporary)
            path = root / "scripts" / "complex.py"
            path.parent.mkdir()
            path.write_text("def too_complex():\n    pass\n", encoding="utf-8")
            finding = {
                "code": "C901",
                "filename": str(path),
                "location": {"row": 1, "column": 5},
                "message": "`too_complex` is too complex (11 > 10)",
            }
            with mock.patch.object(
                CLEAN.subprocess, "run", return_value=ruff_result([finding])
            ) as run:
                measured = CLEAN.measure_python(root)

        self.assertEqual(
            measured["complexity"],
            {"scripts/complex.py:too_complex": 11},
        )
        command = run.call_args.args[0]
        self.assertEqual(
            command,
            [
                "ruff",
                "check",
                "scripts",
                "evals",
                "plugins/sadrazam/company",
                "--select",
                "C901",
                "--config",
                "lint.mccabe.max-complexity=10",
                "--output-format=json",
            ],
        )

    def test_new_grown_shrunk_and_removed_debt_all_require_exact_baseline(self) -> None:
        baseline = {
            "schema_version": 1,
            "violations": [
                {"kind": "module-lines", "target": "evals/run.py", "value": 640},
                {
                    "kind": "function-lines",
                    "target": "evals/run.py:run_evaluations",
                    "value": 125,
                },
            ],
        }
        measured = {
            "module-lines": {"evals/run.py": 641, "scripts/new.py": 401},
            "function-lines": {"evals/run.py:run_evaluations": 100},
            "complexity": {},
            "silent-broad-except": {},
        }

        errors = CLEAN.compare_baseline(measured, baseline)

        self.assertEqual(len(errors), 3)
        self.assertTrue(any("evals/run.py" in error and "640" in error for error in errors))
        self.assertTrue(any("scripts/new.py" in error and "new" in error for error in errors))
        self.assertTrue(any("run_evaluations" in error and "shrunk" in error for error in errors))

        measured["module-lines"].pop("evals/run.py")
        measured["module-lines"].pop("scripts/new.py")
        errors = CLEAN.compare_baseline(measured, baseline)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("evals/run.py" in error and "removed" in error for error in errors))
        self.assertTrue(any("run_evaluations" in error and "shrunk" in error for error in errors))

    def test_silent_broad_exception_pass_is_measured(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-clean-code-") as temporary:
            root = pathlib.Path(temporary)
            path = root / "scripts" / "silent.py"
            path.parent.mkdir()
            path.write_text(
                "def swallow():\n"
                "    try:\n"
                "        risky()\n"
                "    except Exception:\n"
                "        pass\n",
                encoding="utf-8",
            )
            with mock.patch.object(CLEAN.subprocess, "run", return_value=ruff_result([])):
                measured = CLEAN.measure_python(root)

        self.assertEqual(
            measured["silent-broad-except"],
            {"scripts/silent.py:swallow": 1},
        )

    def test_missing_ruff_is_an_actionable_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-clean-code-") as temporary:
            root = pathlib.Path(temporary)
            (root / "scripts").mkdir()
            with mock.patch.object(
                CLEAN.subprocess,
                "run",
                side_effect=FileNotFoundError("ruff"),
            ):
                with self.assertRaisesRegex(CLEAN.CleanCodeError, "install.*requirements-dev"):
                    CLEAN.measure_python(root)


if __name__ == "__main__":
    unittest.main()
