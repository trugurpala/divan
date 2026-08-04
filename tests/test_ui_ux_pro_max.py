from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_ROOT = ROOT / "plugins" / "ui-pack" / "skills" / "ui-ux-pro-max"
SCRIPT = SKILL_ROOT / "scripts" / "search.py"
NESTED_TESTS = SKILL_ROOT / "scripts" / "tests"


def run_cli(*arguments: str, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class UiUxProMaxDistributionTests(unittest.TestCase):
    def test_skill_commands_are_loaded_skill_relative(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("loaded `SKILL.md`", skill)
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}/.claude/skills", skill)
        self.assertEqual(skill.count("<skill-dir>/scripts/search.py"), 11)
        self.assertTrue(SCRIPT.is_file())

    def test_documented_data_counts_match_shipped_csv_rows(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        data = SKILL_ROOT / "data"
        with (data / "ux-guidelines.csv").open(encoding="utf-8", newline="") as file:
            ux_count = sum(1 for _ in csv.DictReader(file))
        with (data / "icons.csv").open(encoding="utf-8", newline="") as file:
            icon_count = sum(1 for _ in csv.DictReader(file))
        self.assertIn(f"{ux_count} UX guidelines", skill)
        self.assertIn(f"{icon_count} icon entries", skill)

    def test_search_runs_from_unrelated_working_directory_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = pathlib.Path(tmp)
            before = sorted(path.relative_to(cwd) for path in cwd.rglob("*"))
            result = run_cli(
                "accessibility contrast keyboard",
                "--domain",
                "ux",
                "--max-results",
                "1",
                "--json",
                cwd=cwd,
            )
            after = sorted(path.relative_to(cwd) for path in cwd.rglob("*"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["count"], 1)
        self.assertEqual(after, before)

    def test_design_system_is_write_free_without_explicit_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = pathlib.Path(tmp)
            result = run_cli(
                "SaaS invoicing dark mode",
                "--design-system",
                "--json",
                cwd=cwd,
            )
            files = [path for path in cwd.rglob("*") if path.is_file()]
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsNone(payload["persistence"])
        self.assertEqual(files, [])

    def test_persist_is_bounded_and_does_not_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = pathlib.Path(tmp) / "unrelated"
            output = pathlib.Path(tmp) / "project"
            cwd.mkdir()
            output.mkdir()
            arguments = (
                "SaaS dashboard",
                "--design-system",
                "--json",
                "--persist",
                "--project-name",
                "Bounded Project",
                "--output-dir",
                str(output),
            )
            first = run_cli(*arguments, cwd=cwd)
            second = run_cli(*arguments, cwd=cwd)
            written = [path for path in output.rglob("*") if path.is_file()]
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout)["persistence"]["status"], "success")
        self.assertEqual(
            json.loads(second.stdout)["persistence"]["status"], "skipped_exists"
        )
        self.assertEqual(
            [path.relative_to(output).as_posix() for path in written],
            ["design-system/bounded-project/MASTER.md"],
        )

    def test_vendored_engine_suite_is_part_of_canonical_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(NESTED_TESTS),
                    "-p",
                    "test_*.py",
                    "-v",
                ],
                cwd=tmp,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("test_dark_query_has_coherent_palette_and_advice", output)
        count = re.search(r"Ran (\d+) tests", output)
        if count is None:
            self.fail(output)
        self.assertGreaterEqual(int(count.group(1)), 45)


if __name__ == "__main__":
    unittest.main()
