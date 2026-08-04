from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowHardeningTests(unittest.TestCase):
    def test_portable_project_action_is_pinned_read_only_and_input_safe(self) -> None:
        text = (
            ROOT / ".github" / "actions" / "divan-project" / "action.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("using: composite", text)
        self.assertIn(
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7",
            text,
        )
        self.assertIn(
            "$GITHUB_ACTION_PATH/../../../plugins/sadrazam/divan_runtime/cli.py",
            text,
        )
        self.assertIn("DIVAN_PROJECT_INPUT: ${{ inputs.project }}", text)
        self.assertNotIn("build_project_runner.py", text)
        self.assertNotIn("github.action_ref", text)
        run_blocks = "\n".join(
            line for line in text.splitlines() if line.lstrip().startswith("run:")
        )
        self.assertNotIn("${{ inputs.", run_blocks)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("deploy", text.casefold())

    def test_pull_request_quality_path_is_secret_free_and_read_only(self) -> None:
        text = (WORKFLOWS / "quality-gate.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request", text)
        self.assertNotIn("pull_request_target", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("environment:", text)

    def test_writable_workflows_default_to_read_only_permissions(self) -> None:
        for filename in (
            "candidate-review.yml",
            "codeql.yml",
            "release.yml",
            "scorecard.yml",
            "wiki-sync.yml",
        ):
            with self.subTest(filename=filename):
                text = (WORKFLOWS / filename).read_text(encoding="utf-8")
                header = text[: text.index("\njobs:")]
                self.assertIn("\npermissions: read-all\n", header)

        codeql = (WORKFLOWS / "codeql.yml").read_text(encoding="utf-8")
        codeql_header = codeql[: codeql.index("\njobs:")]
        self.assertNotIn("security-events: write", codeql_header)
        self.assertIn(
            "  analyze:\n"
            "    runs-on: ubuntu-latest\n"
            "    timeout-minutes: 15\n"
            "    permissions:\n"
            "      contents: read\n"
            "      security-events: write\n",
            codeql,
        )

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

    def test_existing_release_is_rebuilt_only_when_tag_equals_current_main(
        self,
    ) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")

        self.assertIn(
            'remote_tag_commit="$(python scripts/release_tag.py '
            '--remote origin --tag "$tag")"',
            text,
        )
        self.assertIn(
            'if [[ "$remote_tag_commit" != "$GITHUB_SHA" ]]; then',
            text,
        )
        self.assertNotIn('source_commit="$remote_tag_commit"', text)
        self.assertNotIn('git merge-base --is-ancestor', text)
        self.assertNotIn('git worktree add --detach', text)
        self.assertIn(
            'python "$source_root/scripts/build_project_runner.py" '
            '--root "$source_root"',
            text,
        )
        self.assertIn(
            'python "$source_root/scripts/sbom.py" --root "$source_root"',
            text,
        )
        self.assertIn('source_root="$GITHUB_WORKSPACE"', text)
        self.assertIn("TZ: UTC", text)
        self.assertIn("published_release=true", text)
        self.assertIn(
            "if: steps.release_assets.outputs.published_release != 'true'",
            text,
        )
        self.assertIn('"$local_tag_commit" != "$remote_tag_commit"', text)

    def test_release_rechecks_and_creates_remote_tag_before_publication(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")

        self.assertTrue((ROOT / "scripts" / "release_guard.py").is_file())
        self.assertTrue((ROOT / "scripts" / "release_tag.py").is_file())
        release_guard = (ROOT / "scripts" / "release_guard.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("require_exact_assets", release_guard)
        self.assertGreaterEqual(
            text.count(
                'python scripts/release_tag.py --remote origin --tag "$tag"'
            ),
            3,
        )
        self.assertIn(
            'gh api --method POST "repos/$GITHUB_REPOSITORY/git/refs"',
            text,
        )
        self.assertNotIn('git push origin "refs/tags/$tag"', text)
        self.assertIn('"$live_tag_commit" != "$live_main_commit"', text)
        self.assertGreaterEqual(
            text.count(
                'gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" '
                "--jq '.object.sha'"
            ),
            2,
        )
        self.assertIn('test "$live_main_commit" = "$GITHUB_SHA"', text)
        self.assertIn('test "$source_commit" = "$live_main_commit"', text)
        self.assertIn('test "$live_tag_commit" = "$live_main_commit"', text)
        self.assertNotIn("--target", text)
        release_lines = [
            line for line in text.splitlines() if "gh release create" in line
        ]
        self.assertTrue(release_lines)
        self.assertTrue(all("--verify-tag" in line for line in release_lines))
        self.assertGreaterEqual(
            text.count("scripts/release_guard.py immutable"),
            2,
        )
        self.assertGreaterEqual(
            text.count("scripts/release_guard.py ruleset"),
            2,
        )
        self.assertGreaterEqual(
            text.count("scripts/release_guard.py releases"),
            3,
        )
        self.assertGreaterEqual(
            text.count("secrets.DIVAN_RELEASE_ADMIN_TOKEN"),
            2,
        )
        self.assertGreaterEqual(
            text.count("repos/$GITHUB_REPOSITORY/rulesets/20332879"),
            2,
        )
        self.assertEqual(text.count("unset GH_TOKEN"), 3)
        self.assertIn("production-release/DIVAN_RELEASE_ADMIN_TOKEN", text)
        self.assertNotIn('gh release view "$tag"', text)

    def test_scorecard_is_pinned_and_publishes_sarif_with_narrow_permissions(self) -> None:
        text = (WORKFLOWS / "scorecard.yml").read_text(encoding="utf-8")
        self.assertIn("push:\n    branches: [main]", text)
        self.assertIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertIn("security-events: write", text)
        self.assertIn("id-token: write", text)
        self.assertNotIn("contents: write", text)
        self.assertIn(
            "ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc # v2.4.4",
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
        self.assertIn('sbom="$assets_dir/divan-${tag}.spdx.json"', text)
        self.assertIn(
            'python "$source_root/scripts/sbom.py" --root "$source_root"',
            text,
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
        self.assertIn("${{ steps.release_assets.outputs.archive }}", text)
        self.assertIn("${{ steps.release_assets.outputs.sbom }}", text)
        self.assertIn(
            'python "$source_root/scripts/build_project_runner.py" '
            '--root "$source_root"',
            text,
        )
        self.assertIn('runner_sha256="$(sha256sum "$runner"', text)
        self.assertIn('cmp --silent "$runner"', text)
        self.assertIn('gh release create "$tag" "$archive" "$checksum" "$sbom" "$runner"', text)
        self.assertIn("${{ steps.release_assets.outputs.runner }}", text)
        self.assertIn("${{ steps.release_assets.outputs.checksum }}", text)
        self.assertIn("environment: production-release", text)
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        attest = text.index("actions/attest-build-provenance@")
        publish = text.index('gh release create "$tag"')
        self.assertLess(attest, publish)
        self.assertIn('runner_checksum="$assets_dir/divan-project.pyz.sha256"', text)
        self.assertIn('--artifact "$(basename "$runner")=$runner_sha256"', text)
        self.assertIn(
            '--artifact "$(basename "$runner_checksum")=$runner_checksum_sha256"',
            text,
        )

    def test_release_publishes_and_reverifies_clean_host_bootstrap(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")

        self.assertIn('bootstrap="$assets_dir/divan.pyz"', text)
        self.assertIn('bootstrap_checksum="$assets_dir/divan.pyz.sha256"', text)
        self.assertIn(
            'python "$source_root/scripts/build_bootstrap.py" --root "$source_root"',
            text,
        )
        self.assertIn("${{ steps.release_assets.outputs.bootstrap }}", text)
        self.assertIn(
            "${{ steps.release_assets.outputs.bootstrap_checksum }}",
            text,
        )
        self.assertIn('cmp --silent "$bootstrap"', text)
        self.assertIn('cmp --silent "$bootstrap_checksum"', text)
        self.assertIn(
            'gh release download "$tag" --pattern "$(basename "$bootstrap")"',
            text,
        )
        self.assertIn(
            'gh release create "$tag" "$archive" "$checksum" "$sbom" '
            '"$runner" "$runner_checksum" "$bootstrap" "$bootstrap_checksum"',
            text,
        )
        self.assertIn("Bootstrap dosyasını temiz hostta doğrula", text)
        self.assertIn(
            "python scripts/build_bootstrap.py --output \"$RUNNER_TEMP/divan.pyz\"",
            text,
        )
        self.assertIn(
            'python "$RUNNER_TEMP/divan.pyz" doctor --host codex --json',
            text,
        )
        self.assertIn(
            'divan.pyz" install --host codex --profile auto --execute',
            text,
        )
        self.assertIn('divan.pyz" _fallback-remove', text)
        self.assertIn("'42/42 skills' in text", text)

    def test_non_main_dispatch_cannot_reach_publication(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        publish_job = text[text.index("  publish:") :]
        self.assertIn("if: github.ref == 'refs/heads/main'", publish_job)

    def test_release_requires_live_main_tag_and_bundle_exact_equality(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        publish = text[text.index("  publish:") :]

        self.assertNotIn("git merge-base --is-ancestor", text)
        self.assertGreaterEqual(
            publish.count(
                'gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" '
                "--jq '.object.sha'"
            ),
            2,
        )
        self.assertIn('test "$live_main_commit" = "$GITHUB_SHA"', publish)
        self.assertIn('test "$source_commit" = "$live_main_commit"', publish)
        self.assertIn('test "$live_tag_commit" = "$live_main_commit"', publish)

    def test_remote_tag_code_is_isolated_from_release_authority(self) -> None:
        text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        build_start = text.index("  release_build:")
        publish_start = text.index("  publish:")
        build = text[build_start:publish_start]
        publish = text[publish_start:]

        self.assertIn("permissions:\n      contents: read", build)
        self.assertIn("persist-credentials: false", build)
        self.assertIn(
            "actions/upload-artifact@"
            "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1",
            build,
        )
        self.assertIn('python "$source_root/scripts/release.py"', build)
        self.assertIn('python "$source_root/scripts/sbom.py"', build)
        for forbidden in (
            ": write",
            "environment:",
            "secrets.",
            "GH_TOKEN",
            "${{ github.token }}",
        ):
            with self.subTest(job="build", forbidden=forbidden):
                self.assertNotIn(forbidden, build)

        self.assertIn("environment: production-release", publish)
        self.assertIn("contents: write", publish)
        self.assertIn("id-token: write", publish)
        self.assertIn("persist-credentials: false", publish)
        self.assertIn(
            "actions/download-artifact@"
            "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1",
            publish,
        )
        self.assertIn(
            "artifact-ids: ${{ needs.release_build.outputs.artifact_id }}",
            publish,
        )
        self.assertIn("digest-mismatch: error", publish)
        self.assertIn("scripts/release_guard.py bundle", publish)
        self.assertIn(
            'gh api --method POST "repos/$GITHUB_REPOSITORY/git/refs"',
            publish,
        )
        for forbidden in (
            "git worktree",
            "git fetch",
            "git push",
            "$source_root/scripts/",
            "build_project_runner.py",
            "build_bootstrap.py",
            "scripts/sbom.py",
        ):
            with self.subTest(job="publish", forbidden=forbidden):
                self.assertNotIn(forbidden, publish)

    def test_supply_chain_actions_are_attributed_and_release_tracked(self) -> None:
        upstream = (ROOT / "UPSTREAM.md").read_text(encoding="utf-8")
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        manifest = (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        for repository, sha, license_id in (
            ("ossf/scorecard-action", "2d1146689b8cda280b9bc96326124645441f03bc", "Apache-2.0"),
            (
                "actions/dependency-review-action",
                "a1d282b36b6f3519aa1f3fc636f609c47dddb294",
                "MIT",
            ),
            (
                "actions/upload-artifact",
                "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
                "MIT",
            ),
            (
                "actions/download-artifact",
                "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
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
        text = (WORKFLOWS / "compatibility.yml").read_text(encoding="utf-8")
        self.assertIn("@anthropic-ai/claude-code@2.1.215", text)
        self.assertIn("@openai/codex@0.144.6", text)
        self.assertIn('"--host", "both"', text)
        self.assertIn('"scripts/divan.py", "recover"', text)
        self.assertIn('pathlib.Path(environment["CLAUDE_CONFIG_DIR"]).mkdir', text)
        self.assertIn('pathlib.Path(environment["CODEX_HOME"]).mkdir', text)
        self.assertIn("DIVAN_REF: ${{ github.sha }}", text)
        self.assertIn("resolved = shutil.which(host)", text)
        self.assertIn('["cmd.exe", "/d", "/s", "/c", resolved', text)

    def test_primary_audit_runs_lint_types_coverage_and_actionlint(self) -> None:
        text = (WORKFLOWS / "quality-gate.yml").read_text(encoding="utf-8")
        for command in (
            "pip install -r requirements-dev.txt",
            "python scripts/verify.py --coverage",
            "python scripts/standards.py --check",
            "ruff check .",
            "mypy scripts evals plugins/sadrazam/divan_runtime plugins/sadrazam/company",
            '"$(go env GOPATH)/bin/actionlint"',
        ):
            self.assertIn(command, text)
        self.assertNotIn("coverage run -m unittest discover -s tests", text)
        self.assertNotIn("coverage report --fail-under", text)

    def test_dependabot_observes_actions_and_python_dependencies(self) -> None:
        text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: github-actions", text)
        self.assertIn("package-ecosystem: pip", text)
        self.assertIn("directory: /", text)

    def test_primary_audit_keeps_tool_caches_outside_checkout(self) -> None:
        text = (WORKFLOWS / "quality-gate.yml").read_text(encoding="utf-8")
        quality_step = text[
            text.index("      - name: Local quality gates") :
            text.index("      - name: Agent Skills resmi dogrulayici")
        ]
        for declaration in (
            "PYTHONPYCACHEPREFIX: ${{ runner.temp }}/python-cache",
            "RUFF_CACHE_DIR: ${{ runner.temp }}/ruff-cache",
            "MYPY_CACHE_DIR: ${{ runner.temp }}/mypy-cache",
            "COVERAGE_FILE: ${{ runner.temp }}/coverage",
        ):
            self.assertIn(declaration, quality_step)

    def test_python_complexity_budget_is_pinned(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('select = ["E4", "E7", "E9", "F", "I", "C90"]', pyproject)
        self.assertIn("max-complexity = 25", pyproject)

    def test_development_tools_are_exactly_pinned(self) -> None:
        requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("ruff==0.16.0", requirements)
        self.assertIn("mypy==2.3.0", requirements)
        self.assertIn("coverage==7.15.2", requirements)
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        workflow = (WORKFLOWS / "quality-gate.yml").read_text(encoding="utf-8")
        self.assertIn("[tool.ruff]", pyproject)
        self.assertIn("[tool.mypy]", pyproject)
        self.assertIn("[tool.coverage.run]", pyproject)
        self.assertIn("fail_under = 64", pyproject)
        self.assertIn("python scripts/verify.py --coverage", workflow)


if __name__ == "__main__":
    unittest.main()
