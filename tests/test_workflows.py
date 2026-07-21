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

    def test_scorecard_is_pinned_and_publishes_sarif_with_narrow_permissions(self) -> None:
        text = (WORKFLOWS / "scorecard.yml").read_text(encoding="utf-8")
        self.assertIn("push:\n    branches: [main]", text)
        self.assertIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertIn("security-events: write", text)
        self.assertIn("id-token: write", text)
        self.assertNotIn("contents: write", text)
        self.assertIn(
            "ossf/scorecard-action@4eaacf0543bb3f2c246792bd56e8cdeffafb205a # v2.4.3",
            text,
        )
        self.assertIn("results_format: sarif", text)
        self.assertIn("publish_results: true", text)
        self.assertIn("github/codeql-action/upload-sarif@", text)

    def test_dependency_review_is_pull_request_only_and_read_only(self) -> None:
        text = (WORKFLOWS / "dependency-review.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("push:", text)
        self.assertIn("contents: read", text)
        self.assertNotIn(": write", text)
        self.assertIn(
            "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0",
            text,
        )
        self.assertIn("fail-on-severity: moderate", text)

    def test_release_builds_compares_and_attests_archive_and_sbom(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        self.assertIn("id-token: write", text)
        self.assertIn("attestations: write", text)
        self.assertIn("artifact-metadata: write", text)
        self.assertIn('sbom="$RUNNER_TEMP/divan-${tag}.spdx.json"', text)
        self.assertIn(
            'python scripts/sbom.py --output "$sbom" --source-commit "$source_commit"', text
        )
        self.assertIn('sbom_sha256="$(sha256sum "$sbom"', text)
        self.assertIn('cmp --silent "$sbom"', text)
        self.assertIn('gh release download "$tag" --pattern "$(basename "$sbom")"', text)
        self.assertIn('gh release create "$tag" "$archive" "$checksum" "$sbom"', text)
        self.assertNotIn("--clobber", text)
        self.assertIn(
            "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373 # v4.1.1",
            text,
        )
        self.assertIn("${{ steps.release-assets.outputs.archive }}", text)
        self.assertIn("${{ steps.release-assets.outputs.sbom }}", text)

    def test_supply_chain_actions_are_attributed_and_release_tracked(self) -> None:
        upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        manifest = (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        for repository, sha, license_id in (
            ("ossf/scorecard-action", "4eaacf0543bb3f2c246792bd56e8cdeffafb205a", "Apache-2.0"),
            (
                "actions/dependency-review-action",
                "a1d282b36b6f3519aa1f3fc636f609c47dddb294",
                "MIT",
            ),
            (
                "actions/attest-build-provenance",
                "0f67c3f4856b2e3261c31976d6725780e5e4c373",
                "MIT",
            ),
        ):
            with self.subTest(repository=repository):
                self.assertIn(repository, upstream)
                self.assertIn(sha, upstream)
                self.assertIn(repository, licenses)
                self.assertIn(license_id, licenses)
        for path in (
            "scripts/sbom.py",
            ".github/workflows/scorecard.yml",
            ".github/workflows/dependency-review.yml",
            ".github/workflows/release.yml",
        ):
            self.assertIn(f'"path": "{path}"', manifest)

    def test_compatibility_matrix_runs_both_native_host_clis(self) -> None:
        text = (WORKFLOWS / "uyumluluk.yml").read_text(encoding="utf-8")
        self.assertIn("@anthropic-ai/claude-code@2.1.215", text)
        self.assertIn("@openai/codex@0.144.6", text)
        self.assertIn('"--host", "both"', text)
        self.assertIn('"--rollback-transaction"', text)
        self.assertIn('pathlib.Path(environment["CLAUDE_CONFIG_DIR"]).mkdir', text)
        self.assertIn('pathlib.Path(environment["CODEX_HOME"]).mkdir', text)
        self.assertIn("DIVAN_REF: ${{ github.sha }}", text)
        self.assertIn("resolved = shutil.which(host)", text)
        self.assertIn('["cmd.exe", "/d", "/s", "/c", resolved', text)

    def test_primary_audit_runs_lint_types_coverage_and_actionlint(self) -> None:
        text = (WORKFLOWS / "teftis.yml").read_text(encoding="utf-8")
        for command in (
            "pip install -r requirements-dev.txt",
            "python scripts/hijyen.py --check",
            "python scripts/standartlar.py --check",
            "ruff check .",
            "mypy scripts",
            "coverage run -m unittest discover -s tests",
            "coverage report",
            '"$(go env GOPATH)/bin/actionlint"',
        ):
            self.assertIn(command, text)

    def test_python_complexity_budget_is_pinned(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('select = ["E4", "E7", "E9", "F", "I", "C90"]', pyproject)
        self.assertIn("max-complexity = 25", pyproject)

    def test_development_tools_are_exactly_pinned(self) -> None:
        requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("ruff==0.15.22", requirements)
        self.assertIn("mypy==2.3.0", requirements)
        self.assertIn("coverage==7.15.2", requirements)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[tool.ruff]", pyproject)
        self.assertIn("[tool.mypy]", pyproject)
        self.assertIn("[tool.coverage.run]", pyproject)
        self.assertIn("fail_under = 60", pyproject)


if __name__ == "__main__":
    unittest.main()
