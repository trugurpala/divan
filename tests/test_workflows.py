from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowHardeningTests(unittest.TestCase):
    def test_all_actions_are_pinned_to_full_commit_sha(self) -> None:
        mutable: list[str] = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "uses:" not in line or line.lstrip().startswith("#"):
                    continue
                if not re.search(r"uses:\s+[^\s@]+@[0-9a-f]{40}\s+#\s+v\d+", line):
                    mutable.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(mutable, [])

    def test_codeql_workflow_has_init_and_analyze(self) -> None:
        text = (WORKFLOWS / "codeql.yml").read_text(encoding="utf-8")
        self.assertIn("github/codeql-action/init@", text)
        self.assertIn("github/codeql-action/analyze@", text)
        self.assertIn("security-events: write", text)
        self.assertIn("python, javascript-typescript", text)

    def test_release_assets_are_never_clobbered_or_moved_to_another_commit(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        self.assertNotIn("--clobber", text)
        self.assertIn('test "$source_commit" = "$GITHUB_SHA"', text)
        self.assertIn('cmp --silent "$archive"', text)
        self.assertIn('cmp --silent "$checksum"', text)

    def test_compatibility_matrix_runs_both_native_host_clis(self) -> None:
        text = (WORKFLOWS / "uyumluluk.yml").read_text(encoding="utf-8")
        self.assertIn("@anthropic-ai/claude-code@2.1.215", text)
        self.assertIn("@openai/codex@0.144.6", text)
        self.assertIn('"--host", "both"', text)
        self.assertIn('"--rollback-transaction"', text)
        self.assertIn('pathlib.Path(environment["CLAUDE_CONFIG_DIR"]).mkdir', text)
        self.assertIn('pathlib.Path(environment["CODEX_HOME"]).mkdir', text)

    def test_primary_audit_runs_lint_types_coverage_and_actionlint(self) -> None:
        text = (WORKFLOWS / "teftis.yml").read_text(encoding="utf-8")
        for command in (
            "pip install -r requirements-dev.txt",
            "ruff check .",
            "mypy scripts",
            "coverage run -m unittest discover -s tests",
            "coverage report",
            "actionlint",
        ):
            self.assertIn(command, text)

    def test_development_tools_are_exactly_pinned(self) -> None:
        requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("ruff==0.15.22", requirements)
        self.assertIn("mypy==2.3.0", requirements)
        self.assertIn("coverage==7.15.2", requirements)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[tool.ruff]", pyproject)
        self.assertIn("[tool.mypy]", pyproject)
        self.assertIn("[tool.coverage.run]", pyproject)


if __name__ == "__main__":
    unittest.main()
