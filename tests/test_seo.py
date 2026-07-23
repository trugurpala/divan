from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "projects"
SEO_PATH = ROOT / "scripts" / "seo.py"


def load_seo():
    spec = importlib.util.spec_from_file_location("divan_seo", SEO_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SeoPolicyTests(unittest.TestCase):
    def _write_native_evidence(
        self,
        root: pathlib.Path,
        report: dict[str, object],
        *,
        profile: str,
        expected_url: str = "https://example.test/",
    ) -> dict[str, object]:
        plans = {
            row["tool"]: row  # type: ignore[index]
            for row in report["command_plans"]  # type: ignore[union-attr]
        }
        evidence_root = root / ".divan" / "evidence" / "seo"
        evidence_root.mkdir(parents=True)
        executable = evidence_root / "tool.bin"
        executable.write_bytes(b"reviewed executable")
        lighthouse = evidence_root / "lighthouse.json"
        lighthouse.write_text(
            json.dumps(
                {
                    "finalUrl": expected_url,
                    "categories": {
                        name: {"score": 0.99}
                        for name in (
                            "accessibility",
                            "best-practices",
                            "performance",
                            "seo",
                        )
                    },
                }
            ),
            encoding="utf-8",
        )
        lychee = evidence_root / "lychee.json"
        lychee.write_text(
            json.dumps(
                [
                    {"url": f"{expected_url}docs", "status": "OK"},
                    {"url": expected_url, "status": "OK"},
                ]
            ),
            encoding="utf-8",
        )
        def sha(path: pathlib.Path) -> str:
            return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "schema_version": 2,
            "project": report["project"],
            "source_digest": report["project_digest"],
            "profile": profile,
            "expected_url": expected_url,
            "command_plan_digest": report["command_plan_digest"],
            "artifacts": {
                "lighthouse-ci": {
                    "path": lighthouse.relative_to(root).as_posix(),
                    "sha256": sha(lighthouse),
                    "exit_code": 0,
                    "tool_identity": plans["lighthouse-ci"]["identity"],
                    "executable_path": executable.relative_to(root).as_posix(),
                    "executable_sha256": sha(executable),
                },
                "lychee": {
                    "path": lychee.relative_to(root).as_posix(),
                    "sha256": sha(lychee),
                    "exit_code": 0,
                    "tool_identity": plans["lychee"]["identity"],
                    "executable_path": executable.relative_to(root).as_posix(),
                    "executable_sha256": sha(executable),
                },
            },
        }

    def test_fixture_matrix_covers_supported_project_shapes(self) -> None:
        self.assertEqual(
            sorted(path.name for path in FIXTURES.iterdir() if path.is_dir()),
            [
                "library",
                "monorepo",
                "nextjs",
                "python-api",
                "static-site",
                "vite-react",
            ],
        )

    def test_non_public_projects_do_not_receive_web_only_checks(self) -> None:
        seo = load_seo()
        for name in ("library", "python-api"):
            with self.subTest(name=name):
                report = seo.audit_project(FIXTURES / name, profile="standard")
                self.assertFalse(report["applicable"])
                self.assertEqual(report["checks"], [])
                self.assertEqual(report["command_plans"], [])
                self.assertEqual(report["status"], "NOT_APPLICABLE")

    def test_public_web_checks_cover_complete_discovery_contract(self) -> None:
        seo = load_seo()
        report = seo.audit_project(FIXTURES / "static-site", profile="standard")
        self.assertTrue(report["applicable"])
        by_id = {row["id"]: row for row in report["checks"]}
        self.assertEqual(
            set(by_id),
            {
                "canonical",
                "description",
                "hreflang",
                "internal-links",
                "json-ld",
                "open-graph",
                "robots",
                "sitemap",
                "title",
                "twitter-card",
            },
        )
        self.assertTrue(all(row["status"] == "PASS" for row in by_id.values()))
        self.assertEqual(report["static_status"], "PASS")
        self.assertEqual(report["status"], "BLOCKED")
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            base = seo.audit_project(root, profile="standard")
            verified = seo.audit_project(
                root,
                profile="standard",
                evidence=self._write_native_evidence(
                    root, base, profile="standard"
                ),
                expected_url="https://example.test/",
            )
            self.assertEqual(verified["status"], "BLOCKED")
            self.assertEqual(
                verified["evidence_status"], "OBSERVED_UNVERIFIED"
            )

    def test_broken_public_web_fails_closed_with_bounded_static_findings(self) -> None:
        seo = load_seo()
        report = seo.audit_project(FIXTURES / "vite-react", profile="standard")
        self.assertEqual(report["status"], "FAIL")
        by_id = {row["id"]: row for row in report["checks"]}
        self.assertEqual(by_id["canonical"]["status"], "FAIL")
        self.assertEqual(by_id["internal-links"]["status"], "FAIL")
        self.assertIn("missing.html", by_id["internal-links"]["details"])
        self.assertNotIn(str(FIXTURES.resolve()), json.dumps(report))

    def test_thresholds_are_profile_specific_and_report_only_is_explicit(self) -> None:
        seo = load_seo()
        standard = seo.load_policy()["profiles"]["standard"]
        strict = seo.load_policy()["profiles"]["strict"]
        self.assertEqual(
            standard,
            {
                "accessibility": {"minimum": 0.9, "required": True},
                "best-practices": {"minimum": None, "required": False},
                "performance": {"minimum": None, "required": False},
                "seo": {"minimum": 0.9, "required": True},
            },
        )
        self.assertEqual(
            strict,
            {
                "accessibility": {"minimum": 0.95, "required": True},
                "best-practices": {"minimum": 0.9, "required": True},
                "performance": {"minimum": 0.85, "required": True},
                "seo": {"minimum": 0.95, "required": True},
            },
        )

    def test_tool_plans_are_immutable_deterministic_and_do_not_execute(self) -> None:
        seo = load_seo()
        first = seo.audit_project(FIXTURES / "nextjs", profile="strict")
        second = seo.audit_project(FIXTURES / "nextjs", profile="strict")
        self.assertEqual(first["status"], "BLOCKED")
        self.assertTrue(
            all(row["status"] == "NOT_OBSERVED" for row in first["checks"])
        )
        self.assertEqual(first["command_plans"], second["command_plans"])
        plans = {row["tool"]: row for row in first["command_plans"]}
        self.assertEqual(
            plans["lighthouse-ci"]["source_commit"],
            "36e629e9c03a2b328f5996c16f256431c5fef1fe",
        )
        self.assertEqual(
            plans["lychee"]["source_commit"],
            "af73b4e02731e0ff3a678b56769704d689138279",
        )
        self.assertTrue(all(row["execute"] is False for row in plans.values()))
        self.assertEqual(
            plans["lighthouse-ci"]["identity"],
            {
                "ecosystem": "oci",
                "integrity": "sha256:558210c5e422a7babaaa09c285b7469da3f00fac1a9880c37883c65d666a7fc9",
                "npm_integrity": "sha512-TxOH9pFBnmmN7Jmo2Aimxx5UhE8veqXpHfFJDMWsCVxkwh7mGxcAWchGl84mK139SZbbRmerqZ72c+h2nG9/QQ==",
                "package": "patrickhulce/lhci-client",
                "platform": "linux/amd64",
                "source_commit": "36e629e9c03a2b328f5996c16f256431c5fef1fe",
                "version": "0.14.0",
            },
        )
        self.assertEqual(
            plans["lychee"]["identity"]["source_commit"],
            "e85aaf5524b2f808e63bae55e594c843220f10f2",
        )
        self.assertEqual(
            plans["lychee"]["identity"]["integrity"],
            "sha256:1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a",
        )
        self.assertFalse(first["search_console"]["enabled"])
        self.assertEqual(first["search_console"]["status"], "DISABLED")

    def test_required_tool_observations_are_bound_and_enforce_thresholds(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            base = seo.audit_project(root, profile="strict")
            evidence = self._write_native_evidence(root, base, profile="strict")
            lighthouse = root / evidence["artifacts"]["lighthouse-ci"]["path"]
            payload = json.loads(lighthouse.read_text())
            payload["categories"]["performance"]["score"] = 0.84
            lighthouse.write_text(json.dumps(payload), encoding="utf-8")
            evidence["artifacts"]["lighthouse-ci"]["sha256"] = (
                "sha256:" + hashlib.sha256(lighthouse.read_bytes()).hexdigest()
            )
            failed = seo.audit_project(
                root, profile="strict", evidence=evidence,
                expected_url="https://example.test/",
            )
            self.assertEqual(failed["status"], "FAIL")

    def test_discovery_does_not_treat_react_library_or_native_as_public_web(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "react-library",
                        "exports": "./index.js",
                        "peerDependencies": {"react": "19.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                seo.audit_project(root)["status"], "NOT_APPLICABLE"
            )
            (root / "app").mkdir()
            (root / "app" / "index.tsx").write_text("export default null")
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "expo-router-app",
                        "dependencies": {
                            "expo": "53.0.0",
                            "expo-router": "5.0.0",
                            "react-native": "0.79.0",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                seo.audit_project(root)["status"], "NOT_APPLICABLE"
            )

    def test_forged_summary_and_tampered_native_artifacts_are_rejected(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            base = seo.audit_project(root)
            forged = {
                "schema_version": 1,
                "project": base["project"],
                "source_digest": base["project_digest"],
                "profile": "standard",
                "observations": {"lighthouse-ci": {"metrics": {"seo": 1}}},
            }
            self.assertEqual(
                seo.audit_project(
                    root, evidence=forged,
                    expected_url="https://example.test/",
                )["evidence_status"],
                "INVALID",
            )
            evidence = self._write_native_evidence(root, base, profile="standard")
            artifact = root / evidence["artifacts"]["lighthouse-ci"]["path"]
            artifact.write_text('{"forged":true}', encoding="utf-8")
            report = seo.audit_project(
                root, evidence=evidence,
                expected_url="https://example.test/",
            )
            self.assertEqual(report["evidence_status"], "INVALID")
            self.assertTrue(any("SHA256" in row for row in report["evidence_errors"]))

    def test_live_github_readback_is_the_only_pass_authority(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            workflow_content = seo.render_seo_workflow(
                "standard", "https://example.test/"
            ).encode()
            workflow_path = root / ".github" / "workflows" / "divan-seo.yml"
            workflow_path.parent.mkdir(parents=True)
            workflow_path.write_bytes(workflow_content)
            (root / ".gitignore").write_text(".divan/evidence/\n")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=root, check=True
            )
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/acme/site.git"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "fixture"], cwd=root, check=True
            )
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            tree_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
            ).strip()
            base = seo.audit_project(root, expected_url="https://example.test/")
            evidence = self._write_native_evidence(root, base, profile="standard")
            archive = BytesIO()
            with zipfile.ZipFile(archive, "w") as bundle:
                for tool in ("lighthouse-ci", "lychee"):
                    path = root / evidence["artifacts"][tool]["path"]
                    bundle.writestr(path.name, path.read_bytes())
                bundle.writestr(
                    "manifest.json",
                    json.dumps(
                        {
                            "schema_version": 1,
                            "repository": "acme/site",
                            "run_id": "123",
                            "run_attempt": 2,
                            "head_sha": head_sha,
                            "workflow_digest": (
                                "sha256:"
                                + hashlib.sha256(workflow_content).hexdigest()
                            ),
                            "source_identity": {
                                "commit": head_sha,
                                "tree": tree_sha,
                            },
                            "profile": "standard",
                            "expected_url": "https://example.test/",
                            "command_plan_digest": base["command_plan_digest"],
                        }
                    ),
                )
            archive_bytes = archive.getvalue()
            archive_digest = (
                "sha256:" + hashlib.sha256(archive_bytes).hexdigest()
            )
            responses = [
                {"full_name": "acme/site", "html_url": "https://github.com/acme/site"},
                {
                    "id": 123,
                    "run_attempt": 2,
                    "head_sha": head_sha,
                    "conclusion": "success",
                    "status": "completed",
                    "path": ".github/workflows/divan-seo.yml",
                },
                {
                    "sha": "b" * 40,
                    "git_url": "https://api.github.com/repos/acme/site/git/blobs/" + "b" * 40,
                    "encoding": "base64",
                    "content": base64.b64encode(workflow_content).decode("ascii"),
                },
                {"sha": head_sha, "tree": {"sha": tree_sha}},
                {
                    "artifacts": [
                        {
                            "id": 456,
                            "name": "divan-seo-evidence",
                            "expired": False,
                            "digest": archive_digest,
                            "workflow_run": {
                                "id": 123,
                                "head_sha": head_sha,
                            },
                        }
                    ]
                },
                archive_bytes,
            ]
            commands: list[list[str]] = []

            def runner(command: list[str]) -> subprocess.CompletedProcess[object]:
                commands.append(command)
                value = responses.pop(0)
                output = value if isinstance(value, bytes) else json.dumps(value)
                return subprocess.CompletedProcess(command, 0, output, "")

            report = seo.verify_github(
                root,
                repository="acme/site",
                run_id="123",
                run_attempt=2,
                workflow_commit=head_sha,
                expected_url="https://example.test/",
                runner=runner,
            )
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(len(commands), 6)
            self.assertTrue(all(command[:2] == ["gh", "api"] for command in commands))
            self.assertNotIn("provider_run", json.dumps(report))

    def test_live_github_rejects_repo_run_and_artifact_mismatch(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            workflow = root / ".github" / "workflows" / "divan-seo.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                seo.render_seo_workflow("standard", "https://example.test/"),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=root, check=True
            )
            subprocess.run(
                ["git", "remote", "add", "origin",
                 "https://github.com/acme/site.git"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            with self.assertRaisesRegex(
                ValueError, "CLI repository does not match local Git origin"
            ):
                seo.verify_github(
                    root,
                    repository="other/repo",
                    run_id="123",
                    run_attempt=1,
                    workflow_commit="a" * 40,
                    expected_url="https://example.test/",
                )

    def test_native_artifact_url_and_origin_are_exactly_bound(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            base = seo.audit_project(root)
            evidence = self._write_native_evidence(
                root, base, profile="standard",
                expected_url="https://unrelated.test/",
            )
            report = seo.audit_project(
                root, evidence=evidence,
                expected_url="https://example.test/",
            )
            self.assertEqual(report["evidence_status"], "INVALID")
            self.assertEqual(report["static_status"], "PASS")
            self.assertTrue(any("expected URL" in row for row in report["evidence_errors"]))

    def test_lychee_url_prefix_confusion_is_rejected(self) -> None:
        seo = load_seo()
        verdict, errors = seo.native_bytes_verdict(
            json.dumps(
                {
                    "finalUrl": "https://example.test/",
                    "categories": {
                        name: {"score": 1.0}
                        for name in (
                            "accessibility",
                            "best-practices",
                            "performance",
                            "seo",
                        )
                    },
                }
            ).encode(),
            json.dumps(
                [{"url": "https://example.test.evil/path", "status": "OK"}]
            ).encode(),
            "https://example.test/",
            "standard",
        )
        self.assertEqual(verdict, "INVALID")
        self.assertTrue(any("expected URL" in row for row in errors))

    def test_command_plans_include_acquisition_and_digest(self) -> None:
        seo = load_seo()
        report = seo.audit_project(FIXTURES / "nextjs", profile="standard")
        self.assertRegex(report["command_plan_digest"], r"^sha256:[0-9a-f]{64}$")
        for plan in report["command_plans"]:
            self.assertEqual(plan["execute"], False)
            self.assertIn("acquisition", plan)
            self.assertRegex(
                plan["acquisition"]["integrity"],
                r"^(sha256|sha512):",
            )
            self.assertTrue(plan["verification"]["verify_before_observation"])

    def test_command_plan_is_the_exact_workflow_execution_authority(self) -> None:
        seo = load_seo()
        report = seo.audit_project(FIXTURES / "nextjs", profile="standard")
        workflow = seo.render_seo_workflow(
            "standard", "https://example.test/"
        )
        self.assertIn(report["command_plan_digest"], workflow)
        for plan in report["command_plans"]:
            self.assertTrue(plan["runtime"]["acquisition"])
            self.assertTrue(plan["runtime"]["execution"])
            self.assertTrue(plan["outputs"])
            for output in plan["outputs"]:
                self.assertIn(output, workflow)
            for command in (
                *plan["runtime"]["acquisition"],
                *plan["runtime"]["execution"],
            ):
                self.assertIn(
                    seo.render_plan_command(command),
                    workflow,
                    msg=f"{plan['tool']} command is not rendered canonically",
                )

    def test_lychee_release_member_contract_is_exact_and_nested(self) -> None:
        policy = json.loads(
            (ROOT / "registry" / "seo-policy.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "seo"
             / "lychee-0.24.2-members.json").read_text(encoding="utf-8")
        )
        acquisition = policy["tools"]["lychee"]["acquisition"]
        self.assertEqual(acquisition["members"], fixture)
        self.assertEqual(
            acquisition["executable"],
            "lychee-x86_64-unknown-linux-gnu/lychee",
        )
        workflow = load_seo().render_seo_workflow(
            "standard", "https://example.test/"
        )
        self.assertIn("/tmp/divan-lychee/lychee-x86_64-unknown-linux-gnu/lychee", workflow)
        self.assertIn("member.issym() or member.islnk()", workflow)
        self.assertIn("archive members do not match reviewed contract", workflow)

    def test_lighthouse_identity_matches_oci_config_and_runtime_fixture(self) -> None:
        policy = json.loads(
            (ROOT / "registry" / "seo-policy.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "tests" / "fixtures" / "seo"
             / "lhci-client-558210c5.json").read_text(encoding="utf-8")
        )
        tool = policy["tools"]["lighthouse-ci"]
        self.assertEqual(tool["identity"]["version"], fixture["runtime_version"])
        self.assertEqual(
            tool["identity"]["source_commit"], fixture["source_git_head"]
        )
        self.assertEqual(
            tool["identity"]["npm_integrity"], fixture["npm_integrity"]
        )
        self.assertEqual(
            tool["acquisition"]["image"], fixture["image"]
        )
        self.assertEqual(
            tool["acquisition"]["config_digest"], fixture["config_digest"]
        )
        self.assertIn(
            fixture["history_install"],
            tool["acquisition"]["reviewed_history"],
        )
        workflow = load_seo().render_seo_workflow(
            "standard", "https://example.test/"
        )
        version_command = "lhci --version"
        collect_command = "lhci collect"
        self.assertIn(
            f'test "$(docker run --rm {fixture["image"]} '
            f'{version_command})" = "{fixture["runtime_version"]}"',
            workflow,
        )
        self.assertLess(
            workflow.index(version_command), workflow.index(collect_command)
        )

    def test_managed_expected_url_is_loaded_and_override_must_match(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            (root / ".divan").mkdir()
            (root / ".divan" / "seo-tools.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "expected_url": "https://example.test/",
                    }
                ),
                encoding="utf-8",
            )
            report = seo.audit_project(root)
            self.assertEqual(report["expected_url"], "https://example.test/")
            with self.assertRaisesRegex(ValueError, "managed expected_url"):
                seo.audit_project(
                    root, expected_url="https://different.test/"
                )

    def test_markup_and_deployment_files_are_semantically_validated(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "site"
            shutil.copytree(FIXTURES / "static-site", root)
            html = (root / "index.html").read_text(encoding="utf-8")
            html = html.replace(
                '<link rel="canonical" href="https://example.test/">',
                '<a rel="canonical" href="/relative">',
            )
            html = html.replace(
                '"@context":"https://schema.org"',
                '"@context":"https://invalid.test"',
            )
            html = html.replace(
                'content="https://example.test/social.png"',
                'content="/relative-social.png"',
            )
            (root / "index.html").write_text(html, encoding="utf-8")
            (root / "robots.txt").write_text("hello", encoding="utf-8")
            (root / "sitemap.xml").write_text("<root/>", encoding="utf-8")
            report = seo.audit_project(root)
            by_id = {row["id"]: row["status"] for row in report["checks"]}
            self.assertEqual(by_id["canonical"], "FAIL")
            self.assertEqual(by_id["json-ld"], "FAIL")
            self.assertEqual(by_id["open-graph"], "FAIL")
            self.assertEqual(by_id["robots"], "FAIL")
            self.assertEqual(by_id["sitemap"], "FAIL")

    def test_traversal_limits_and_symlinks_fail_closed(self) -> None:
        seo = load_seo()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for number in range(70):
                (root / f"d{number:03d}").mkdir()
            with self.assertRaisesRegex(ValueError, "directory limit"):
                seo.audit_project(root)
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "real"
            target.mkdir()
            link = root / "linked"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest("directory symlink unavailable")
            with self.assertRaisesRegex(ValueError, "symlink"):
                seo.audit_project(link)

    def test_search_console_opt_in_requires_complete_read_only_capability(self) -> None:
        seo = load_seo()
        incomplete = {"enabled": True, "account": "owner"}
        report = seo.audit_project(
            FIXTURES / "static-site", search_console=incomplete
        )
        self.assertEqual(report["search_console"]["status"], "BLOCKED")
        self.assertEqual(report["status"], "BLOCKED")
        configured = {
            "enabled": True,
            "account": "owner",
            "property": "sc-domain:example.test",
            "auth": "provider-managed",
            "capability": {
                "id": "google-search-console",
                "available": True,
                "operations": ["inspect"],
            },
        }
        report = seo.audit_project(
            FIXTURES / "static-site", search_console=configured
        )
        self.assertEqual(
            report["search_console"]["status"], "CONFIGURED_UNVERIFIED"
        )
        self.assertNotIn("mutate", json.dumps(report["search_console"]))

    def test_divan_pages_roots_ship_robots_and_sitemap(self) -> None:
        seo = load_seo()
        for relative in ("docs", "site"):
            with self.subTest(relative=relative):
                report = seo.audit_project(ROOT / relative)
                by_id = {row["id"]: row["status"] for row in report["checks"]}
                self.assertEqual(by_id["robots"], "PASS")
                self.assertEqual(by_id["sitemap"], "PASS")

    def test_cli_emits_stable_json_and_rejects_unknown_profile(self) -> None:
        command = [
            sys.executable,
            str(SEO_PATH),
            "audit",
            "--project",
            str(FIXTURES / "library"),
            "--profile",
            "standard",
            "--json",
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "NOT_APPLICABLE")
        self.assertTrue(completed.stdout.endswith("\n"))
        failed = subprocess.run(
            [*command[:-3], "--profile", "unsafe", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(failed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
