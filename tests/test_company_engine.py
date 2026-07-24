import importlib.util
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPANY = ROOT / "plugins" / "sadrazam" / "company"
ENGINE_PATH = COMPANY / "engine.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("divan_company_engine", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Divan company engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompanyContractTests(unittest.TestCase):
    def test_contracts_are_bilingual_unique_and_reference_real_skills(self) -> None:
        engine = load_engine()
        contracts = engine.load_contracts(COMPANY)

        self.assertEqual(len(contracts.roles), 12)
        self.assertEqual(len(contracts.workflows), 11)
        self.assertGreaterEqual(len(contracts.frameworks), 5)
        self.assertGreaterEqual(len(contracts.impact_rules), 6)

        available = {
            package.name: {
                skill.parent.name
                for skill in (package / "skills").glob("*/SKILL.md")
            }
            for package in (ROOT / "plugins").iterdir()
            if package.is_dir()
        }
        for role in contracts.roles.values():
            self.assertTrue(role.label["en"])
            self.assertTrue(role.label["tr"])
            self.assertTrue(role.inputs)
            self.assertTrue(role.outputs)
            self.assertTrue(role.gates)
            for skill in role.skills:
                self.assertIn(skill.package, available)
                self.assertIn(skill.skill, available[skill.package])

    def test_malformed_role_reference_is_rejected(self) -> None:
        engine = load_engine()
        with tempfile.TemporaryDirectory() as temporary:
            target = pathlib.Path(temporary)
            for source in COMPANY.glob("*.json"):
                (target / source.name).write_text(
                    source.read_text(encoding="utf-8"), encoding="utf-8"
                )
            workflows = json.loads(
                (target / "workflows.json").read_text(encoding="utf-8")
            )
            workflows["workflows"][0]["roles"].append("missing-role")
            (target / "workflows.json").write_text(
                json.dumps(workflows), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "unknown role"):
                engine.load_contracts(target)

    def test_sadrazam_routes_natural_language_through_company_os(self) -> None:
        skill = (
            ROOT / "plugins" / "sadrazam" / "skills" / "sadrazam" / "SKILL.md"
        ).read_text(encoding="utf-8")
        command = ROOT / "plugins" / "sadrazam" / "commands" / "company.md"

        for required in (
            "Company OS",
            "${CLAUDE_PLUGIN_ROOT}",
            "smallest qualified team",
            "impact",
            "natural language",
            "core-pack",
            "ui-pack",
            "react-pack",
            "zanaat-pack",
        ):
            self.assertIn(required, skill)
        self.assertTrue(command.is_file())
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command.read_text(encoding="utf-8"))
        self.assertIn("scripts/release.py", skill)
        self.assertNotIn("scripts/yayin.py", skill)


class ProjectIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_engine()
        self.contracts = self.engine.load_contracts(COMPANY)

    def test_nextjs_ui_task_selects_core_ui_and_react_without_zanaat(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {
                            "next": "15.4.0",
                            "react": "19.1.0",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = self.engine.plan_intent(
                "Redesign the responsive onboarding dashboard", project, self.contracts
            )

        self.assertEqual(result["workflow"], "ui-delivery")
        self.assertEqual(result["frameworks"], ["nextjs", "react"])
        self.assertEqual(
            set(result["packages"]), {"core-pack", "react-pack", "ui-pack"}
        )
        self.assertIn("ux-designer", result["roles"])
        self.assertIn("frontend-engineer", result["roles"])
        self.assertIn("qa-engineer", result["roles"])

    def test_build_api_does_not_match_ui_substring(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.engine.plan_intent(
                "build an API", pathlib.Path(temporary), self.contracts
            )
        self.assertEqual(result["workflow"], "feature-delivery")
        self.assertNotIn("ui-pack", result["packages"])

    def test_static_site_does_not_add_ui_pack_to_backend_work(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "index.html").write_text("<main></main>", encoding="utf-8")
            result = self.engine.plan_intent(
                "add authentication to backend", project, self.contracts
            )
        self.assertNotIn("ui-pack", result["packages"])
        self.assertFalse(any("browser" in check for check in result["checks"]))

    def test_python_backend_bug_keeps_native_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            result = self.engine.plan_intent(
                "fix a Python backend bug", project, self.contracts
            )
        self.assertIn("python -m unittest discover", result["checks"])

    def test_react_feature_keeps_react_pack_when_not_backend_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"dependencies": {"react": "19.1.0"}}),
                encoding="utf-8",
            )
            result = self.engine.plan_intent(
                "add state management", project, self.contracts
            )
        self.assertIn("react-pack", result["packages"])

    def test_integration_task_selects_zanaat_mcp_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\nname='connector'\n", encoding="utf-8"
            )
            result = self.engine.plan_intent(
                "Build an MCP integration for our external API",
                project,
                self.contracts,
            )

        self.assertEqual(result["workflow"], "integration-delivery")
        self.assertIn("zanaat-pack", result["packages"])
        self.assertIn(
            {"package": "zanaat-pack", "skill": "mcp-builder"},
            result["skills"],
        )
        self.assertIn("integration-engineer", result["roles"])

    def test_inspection_is_bounded_and_does_not_execute_project_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "index.html").write_text("<main>Divan</main>", encoding="utf-8")
            (project / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
            marker = project / "must-not-run"
            (project / "setup.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n",
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

            self.assertEqual(result["frameworks"], ["python", "static-web"])
            self.assertFalse(marker.exists())

    def test_project_path_must_be_a_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = pathlib.Path(temporary) / "missing"
            with self.assertRaisesRegex(ValueError, "project directory"):
                self.engine.inspect_project(missing, self.contracts)

    def test_turkish_unicode_and_compound_intent_compose_ranked_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "packageManager": "pnpm@10.13.1",
                        "scripts": {"build": "next build", "test": "vitest"},
                        "dependencies": {"next": "15.4.0", "react": "19.1.0"},
                    }
                ),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")

            result = self.engine.plan_intent(
                "GÜVENLİK testlerini çalıştır, Next.js uygulamasını deploy et "
                "ve SEO’yu iyileştir",
                project,
                self.contracts,
            )

        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["workflow"], "security-delivery")
        self.assertEqual(result["primary_workflow"], "security-delivery")
        self.assertEqual(
            result["workflows"],
            [
                "security-delivery",
                "testing-delivery",
                "deployment-delivery",
                "seo-delivery",
            ],
        )
        self.assertEqual(result["providers"], ["context7", "local", "vercel"])
        self.assertTrue(result["required_evidence"])
        self.assertIn("public-web", result["project_types"])
        self.assertEqual(result["package_managers"], ["pnpm"])
        self.assertEqual(
            [row["command"] for row in result["commands"]],
            ["pnpm run build", "pnpm run test"],
        )

    def test_english_and_turkish_i_variants_match_canonical_keywords(self) -> None:
        cases = {
            "AÇIK düzelt": "security-delivery",
            "SINAMA yap": "testing-delivery",
            "DAĞITIM yap": "deployment-delivery",
            "YAYINA AL": "deployment-delivery",
            "INTEGRATION kur": "integration-delivery",
        }
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            for intent, expected in cases.items():
                with self.subTest(intent=intent):
                    result = self.engine.plan_intent(
                        intent, project, self.contracts
                    )
                    self.assertEqual(result["primary_workflow"], expected)

    def test_longest_phrase_suppresses_subsumed_workflow_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            phrase = self.engine.plan_intent(
                "Run the integration test", project, self.contracts
            )
            compound = self.engine.plan_intent(
                "Build an integration and tests", project, self.contracts
            )

        self.assertEqual(phrase["workflows"], ["testing-delivery"])
        self.assertEqual(
            compound["workflows"],
            ["integration-delivery", "testing-delivery", "feature-delivery"],
        )

    def test_nested_workspaces_discover_node_managers_and_native_scripts(self) -> None:
        lockfiles = {
            "apps/npm-app": ("package-lock.json", "npm run build"),
            "apps/pnpm-app": ("pnpm-lock.yaml", "pnpm run test"),
            "packages/yarn-lib": ("yarn.lock", "yarn run lint"),
            "tools/bun-tool": ("bun.lock", "bun run check"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"private": True, "workspaces": ["apps/*", "packages/*"]}),
                encoding="utf-8",
            )
            for relative, (lockfile, expected) in lockfiles.items():
                workspace = project / relative
                workspace.mkdir(parents=True)
                script = expected.rsplit(" ", 1)[-1]
                (workspace / "package.json").write_text(
                    json.dumps({"scripts": {script: "never execute this"}}),
                    encoding="utf-8",
                )
                (workspace / lockfile).write_text("", encoding="utf-8")

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(
            [row["path"] for row in result["workspaces"]],
            [".", "apps/npm-app", "apps/pnpm-app", "packages/yarn-lib", "tools/bun-tool"],
        )
        self.assertEqual(result["package_managers"], ["bun", "npm", "pnpm", "yarn"])
        self.assertEqual(
            {row["workspace"]: row["command"] for row in result["commands"]},
            {
                "apps/npm-app": "npm run build",
                "apps/pnpm-app": "pnpm run test",
                "packages/yarn-lib": "yarn run lint",
                "tools/bun-tool": "bun run check",
            },
        )
        self.assertIn("monorepo", result["project_types"])

    def test_nested_workspace_inherits_root_lockfile_package_manager(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            workspace = project / "apps" / "web"
            workspace.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"private": True, "workspaces": ["apps/*"]}),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text(
                "lockfileVersion: '9.0'\n", encoding="utf-8"
            )
            (workspace / "package.json").write_text(
                json.dumps({"scripts": {"build": "next build"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertIn(
            {
                "workspace": "apps/web",
                "manager": "pnpm",
                "name": "build",
                "command": "pnpm run build",
            },
            result["commands"],
        )

    def test_nested_workspace_inherits_nearest_workspace_package_manager(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            owner = project / "apps" / "suite"
            child = owner / "web"
            child.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"private": True, "workspaces": ["apps/*"]}),
                encoding="utf-8",
            )
            (project / "package-lock.json").write_text("{}", encoding="utf-8")
            (owner / "package.json").write_text(
                json.dumps(
                    {
                        "packageManager": "pnpm@10.13.1",
                        "workspaces": ["web"],
                    }
                ),
                encoding="utf-8",
            )
            (child / "package.json").write_text(
                json.dumps({"scripts": {"child": "never execute this"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        child_commands = [
            row for row in result["commands"] if row["workspace"] == "apps/suite/web"
        ]
        self.assertEqual(
            child_commands,
            [
                {
                    "workspace": "apps/suite/web",
                    "manager": "pnpm",
                    "name": "child",
                    "command": "pnpm run child",
                }
            ],
        )

    def test_nested_node_workspace_ignores_intermediate_python_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            python_workspace = project / "services" / "python"
            child = python_workspace / "web"
            child.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"packageManager": "pnpm@10.13.1"}),
                encoding="utf-8",
            )
            (python_workspace / "pyproject.toml").write_text(
                "[project]\nname='api'\n",
                encoding="utf-8",
            )
            (child / "package.json").write_text(
                json.dumps({"scripts": {"build": "never execute this"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertIn(
            {
                "workspace": "services/python/web",
                "manager": "pnpm",
                "name": "build",
                "command": "pnpm run build",
            },
            result["commands"],
        )

    def test_node_workspace_without_manager_evidence_keeps_searching(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            owner = project / "apps" / "suite"
            child = owner / "web"
            child.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"packageManager": "pnpm@10.13.1"}),
                encoding="utf-8",
            )
            (owner / "package.json").write_text(
                json.dumps({"private": True}),
                encoding="utf-8",
            )
            (child / "package.json").write_text(
                json.dumps({"scripts": {"build": "never execute this"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertIn(
            {
                "workspace": "apps/suite/web",
                "manager": "pnpm",
                "name": "build",
                "command": "pnpm run build",
            },
            result["commands"],
        )

    def test_conflicting_intermediate_node_workspace_blocks_inheritance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            owner = project / "apps" / "suite"
            child = owner / "web"
            child.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"packageManager": "pnpm@10.13.1"}),
                encoding="utf-8",
            )
            (owner / "package.json").write_text(
                json.dumps({"private": True}),
                encoding="utf-8",
            )
            (owner / "package-lock.json").write_text("{}", encoding="utf-8")
            (owner / "yarn.lock").write_text("", encoding="utf-8")
            (child / "package.json").write_text(
                json.dumps({"scripts": {"build": "never execute this"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(
            result["package_manager_conflicts"],
            [
                {
                    "workspace": "apps/suite",
                    "declared": None,
                    "lockfile_managers": ["npm", "yarn"],
                    "selected": None,
                    "reason": "multiple-lockfiles",
                }
            ],
        )
        self.assertEqual(
            [
                row
                for row in result["commands"]
                if row["workspace"] == "apps/suite/web"
            ],
            [],
        )

    def test_invalid_intermediate_node_manager_blocks_inheritance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            owner = project / "apps" / "suite"
            child = owner / "web"
            child.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"packageManager": "pnpm@10.13.1"}),
                encoding="utf-8",
            )
            (owner / "package.json").write_text(
                json.dumps({"packageManager": "pip@24.0"}),
                encoding="utf-8",
            )
            (child / "package.json").write_text(
                json.dumps({"scripts": {"build": "never execute this"}}),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(
            result["package_manager_conflicts"],
            [
                {
                    "workspace": "apps/suite",
                    "declared": "pip",
                    "lockfile_managers": [],
                    "selected": None,
                    "reason": "invalid-declaration",
                }
            ],
        )
        self.assertEqual(
            [
                row
                for row in result["commands"]
                if row["workspace"] == "apps/suite/web"
            ],
            [],
        )

    def test_package_manager_conflicts_are_deterministic_and_unambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            multiple = project / "packages" / "multiple"
            multiple.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "packageManager": "pnpm@10.13.1",
                        "scripts": {"build": "never execute this"},
                    }
                ),
                encoding="utf-8",
            )
            (project / "package-lock.json").write_text("{}", encoding="utf-8")
            (multiple / "package.json").write_text(
                json.dumps({"scripts": {"test": "never execute this"}}),
                encoding="utf-8",
            )
            (multiple / "package-lock.json").write_text("{}", encoding="utf-8")
            (multiple / "yarn.lock").write_text("", encoding="utf-8")

            result = self.engine.inspect_project(project, self.contracts)
            plan = self.engine.plan_intent("test", project, self.contracts)

        self.assertIn("package_manager_conflicts", result)
        self.assertEqual(
            result["package_manager_conflicts"],
            [
                {
                    "workspace": ".",
                    "declared": "pnpm",
                    "lockfile_managers": ["npm"],
                    "selected": "pnpm",
                    "reason": "declaration-lockfile-mismatch",
                },
                {
                    "workspace": "packages/multiple",
                    "declared": None,
                    "lockfile_managers": ["npm", "yarn"],
                    "selected": None,
                    "reason": "multiple-lockfiles",
                },
            ],
        )
        self.assertEqual(
            [row["command"] for row in result["commands"]],
            ["pnpm run build"],
        )
        self.assertEqual(
            plan["package_manager_conflicts"],
            result["package_manager_conflicts"],
        )

    def test_manifest_script_names_cannot_inject_shell_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package-lock.json").write_text("{}", encoding="utf-8")
            (project / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {
                            "--help": "never execute this",
                            "-c": "never execute this",
                            "test": "vitest",
                            "test; echo unsafe": "never execute this",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(
            [row["command"] for row in result["commands"]],
            ["npm run test"],
        )

    def test_resolved_outside_candidate_fails_pure_containment_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            container = pathlib.Path(temporary)
            project = (container / "project").resolve()
            project.mkdir()
            outside = (container / "outside.txt").resolve()
            outside.write_text("outside", encoding="utf-8")

            self.assertTrue(hasattr(self.engine, "_is_project_contained"))
            self.assertFalse(self.engine._is_project_contained(project, outside))

    @unittest.skipIf(os.name == "nt", "file symlink coverage runs on POSIX")
    def test_resolved_marker_symlink_cannot_escape_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            container = pathlib.Path(temporary)
            project = container / "project"
            project.mkdir()
            external = container / "main.go"
            external.write_text("package main\n", encoding="utf-8")
            try:
                (project / "main.go").symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            (project / "go.mod").write_text(
                "module example.test/service\n", encoding="utf-8"
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["project_types"], ["library"])

    def test_requirements_use_exact_distribution_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "requirements.txt").write_text(
                "# django is not used\n"
                "--index-url https://packages.example.invalid/simple\n"
                "-r base.txt\n"
                "fastapi-not-installed==1\n"
                "django-extra>=1\n"
                "django is not used\n"
                "fastapi!!!\n"
                "django/../local\n"
                "django[broken\n"
                "fastapi=>0.115\n"
                "django===\n",
                encoding="utf-8",
            )

            negative = self.engine.inspect_project(project, self.contracts)

            (project / "requirements.txt").write_text(
                "Django==5.2\n"
                "fastapi>=0.115,<1\n"
                "Django[postgres]>=5; python_version >= '3.11'\n"
                "fastapi @ https://packages.example.invalid/fastapi.whl\n",
                encoding="utf-8",
            )
            positive = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(negative["frameworks"], ["python"])
        self.assertNotIn("service", negative["project_types"])
        self.assertTrue(
            {"django", "fastapi", "python"}.issubset(positive["frameworks"])
        )
        self.assertEqual(positive["project_types"], ["application", "service"])

    def test_requirement_rows_require_complete_valid_syntax(self) -> None:
        accepted = {
            "django==5.2": "django",
            "fastapi>=0.115,<1": "fastapi",
            "django==1.2rc1": "django",
            "django==1.2.post1": "django",
            "django==1.2.dev1": "django",
            "django==1.2+local.1": "django",
            "fastapi!=1.2+local.1": "fastapi",
            "django==1.2.*": "django",
            "fastapi!=1.2.*": "fastapi",
            "fastapi~=1.4": "fastapi",
            "django>=1!2": "django",
            "django==v1.2": "django",
            "django===foo": "django",
            "django===foobar": "django",
            "django==1.0-rc1": "django",
            "django==1.0c1": "django",
            "django==1.0alpha1": "django",
            "django==1.0beta2": "django",
            "django==1.0pre3": "django",
            "django==1.0preview4": "django",
            "django==1.0_rev2": "django",
            "django==1.0r3": "django",
            "django==1.0-2": "django",
            "Django[postgres]>=5; python_version >= '3.11'": "django",
            "fastapi; os_name == 'posix'": "fastapi",
            "fastapi @ https://packages.example.invalid/fastapi.whl": "fastapi",
        }
        rejected = (
            "django is not used",
            "fastapi!!!",
            "django/../local",
            "django[broken",
            "django[]",
            "fastapi=>0.115",
            "django===",
            "django; not a marker",
            "django==1*2",
            "django>=1!!",
            "django~=1",
            "django>=1.*",
            "django<1.*",
            "django<=1.*",
            "django>1.*",
            "django~=1.0.*",
            "django>=1.0+local",
            "django>1.0+local",
            "django<=1.0+local",
            "django<1.0+local",
            "django~=1.0+local",
            "django===foo bar",
            "django===foo;",
            "django===foo(",
            "django===foo)",
        )

        for requirement, expected in accepted.items():
            with self.subTest(requirement=requirement):
                self.assertEqual(
                    self.engine._requirement_name(requirement), expected
                )
        for requirement in rejected:
            with self.subTest(requirement=requirement):
                self.assertIsNone(self.engine._requirement_name(requirement))

    def test_parenthesized_requirement_specifier_boundaries(self) -> None:
        accepted = (
            "django (>=1.0)",
            "django(>=1.0)",
            "django ( >=1.0, <2 )",
            "django(>=1.0); python_version >= '3.11'",
            "django (>=1.0) ; os_name == 'posix'",
            "Django[postgres] (>=5, <6); python_version >= '3.11'",
            "django(===foo)",
        )
        rejected = (
            "django()",
            "django(>=1.0",
            "django>=1.0)",
            "django((>=1.0))",
            "django(>=1.0))",
            "django(>=1.0) garbage",
            "django(>=1.0)(<2)",
            "django(>=1.0; python_version >= '3.11')",
        )

        for requirement in accepted:
            with self.subTest(requirement=requirement):
                self.assertEqual(
                    self.engine._requirement_name(requirement), "django"
                )
        for requirement in rejected:
            with self.subTest(requirement=requirement):
                self.assertIsNone(self.engine._requirement_name(requirement))

    def test_marker_nesting_over_limit_is_invalid_evidence(self) -> None:
        marker = (
            "(" * 33
            + "python_version == '3.11'"
            + ")" * 33
        )
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "requirements.txt").write_text(
                f"django; {marker}\n", encoding="utf-8"
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["frameworks"], ["python"])

    def test_recursive_marker_input_never_crashes_inspection(self) -> None:
        marker = (
            "(" * 500
            + "python_version == '3.11'"
            + ")" * 500
        )
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "requirements.txt").write_text(
                f"django; {marker}\n", encoding="utf-8"
            )

            try:
                result = self.engine.inspect_project(project, self.contracts)
            except RecursionError:
                self.fail("recursive marker input escaped fail-closed parsing")

        self.assertEqual(result["frameworks"], ["python"])

    def test_pyproject_dependency_tables_are_parsed_without_prose_scanning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\n"
                "name='semantic'\n"
                "description='django and fastapi are not dependencies'\n",
                encoding="utf-8",
            )
            (project / "setup.py").write_text(
                "# prose mentioning fastapi and django\n",
                encoding="utf-8",
            )

            negative = self.engine.inspect_project(project, self.contracts)

            (project / "pyproject.toml").write_text(
                "[project]\n"
                "name='semantic'\n"
                "dependencies=['Django>=5']\n"
                "[project.optional-dependencies]\n"
                "api=['FastAPI[standard]>=0.115']\n"
                "[tool.poetry.dependencies]\n"
                "python='^3.11'\n"
                "[tool.poetry.group.dev.dependencies]\n"
                "django-debug-toolbar='^5'\n",
                encoding="utf-8",
            )

            positive = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(negative["frameworks"], ["python"])
        self.assertTrue(
            {"django", "fastapi", "python"}.issubset(positive["frameworks"])
        )
        self.assertEqual(positive["project_types"], ["application", "service"])

    def test_project_types_follow_language_entrypoint_and_library_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            fixtures = {
                "python-lib": (
                    "pyproject.toml",
                    "[project]\n"
                    "name='lib'\n"
                    "[build-system]\n"
                    "requires=['setuptools']\n"
                    "build-backend='setuptools.build_meta'\n",
                ),
                "python-app": (
                    "pyproject.toml",
                    "[project]\nname='app'\n[project.scripts]\napp='app:main'\n",
                ),
                "python-main": (
                    "pyproject.toml",
                    "[project]\nname='main-package'\n",
                ),
                "go-lib": ("go.mod", "module example.test/library\n"),
                "go-app": ("go.mod", "module example.test/application\n"),
                "rust-lib": (
                    "Cargo.toml",
                    "[package]\nname='rust-lib'\nversion='0.1.0'\n",
                ),
                "rust-bin": (
                    "Cargo.toml",
                    "[package]\nname='rust-bin'\nversion='0.1.0'\n",
                ),
                "rust-both": (
                    "Cargo.toml",
                    "[package]\nname='rust-both'\nversion='0.1.0'\n",
                ),
            }
            for relative, (manifest, contents) in fixtures.items():
                workspace = project / relative
                workspace.mkdir()
                (workspace / manifest).write_text(contents, encoding="utf-8")
            (project / "go-app" / "cmd" / "server").mkdir(parents=True)
            (project / "go-app" / "cmd" / "server" / "main.go").write_text(
                "package main\n", encoding="utf-8"
            )
            python_main = (
                project / "python-main" / "src" / "main_package" / "__main__.py"
            )
            python_main.parent.mkdir(parents=True)
            python_main.write_text("raise SystemExit(0)\n", encoding="utf-8")
            for relative, markers in {
                "rust-lib": ("src/lib.rs",),
                "rust-bin": ("src/main.rs",),
                "rust-both": ("src/lib.rs", "src/main.rs"),
            }.items():
                for marker in markers:
                    target = project / relative / marker
                    target.parent.mkdir(exist_ok=True)
                    target.write_text("", encoding="utf-8")

            result = self.engine.inspect_project(project, self.contracts)

        types = {row["path"]: row["project_types"] for row in result["workspaces"]}
        self.assertEqual(types["python-lib"], ["library"])
        self.assertEqual(types["python-app"], ["application"])
        self.assertEqual(types["python-main"], ["application"])
        self.assertEqual(types["go-lib"], ["library"])
        self.assertEqual(types["go-app"], ["application"])
        self.assertEqual(types["rust-lib"], ["library"])
        self.assertEqual(types["rust-bin"], ["application"])
        self.assertEqual(types["rust-both"], ["application", "library"])

    def test_project_types_ignore_incidental_python_and_go_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            fixtures = {
                "fastapi-service": (
                    "[project]\n"
                    "name='api'\n"
                    "dependencies=['fastapi']\n"
                    "[build-system]\n"
                    "requires=['setuptools']\n"
                    "build-backend='setuptools.build_meta'\n"
                ),
                "name-only": "[project]\nname='metadata-only'\n",
                "fixture-main-library": (
                    "[project]\n"
                    "name='fixture-lib'\n"
                    "[build-system]\n"
                    "requires=['setuptools']\n"
                    "build-backend='setuptools.build_meta'\n"
                ),
                "root-main": "[project]\nname='root-main'\n",
                "package-main": "[project]\nname='package-main'\n",
            }
            for relative, contents in fixtures.items():
                workspace = project / relative
                workspace.mkdir()
                (workspace / "pyproject.toml").write_text(
                    contents, encoding="utf-8"
                )
            fixture_main = (
                project
                / "fixture-main-library"
                / "tests"
                / "fixtures"
                / "demo"
                / "__main__.py"
            )
            fixture_main.parent.mkdir(parents=True)
            fixture_main.write_text("raise SystemExit(0)\n", encoding="utf-8")
            (project / "root-main" / "__main__.py").write_text(
                "raise SystemExit(0)\n", encoding="utf-8"
            )
            package_main = (
                project
                / "package-main"
                / "src"
                / "package_main"
                / "__main__.py"
            )
            package_main.parent.mkdir(parents=True)
            package_main.write_text("raise SystemExit(0)\n", encoding="utf-8")
            for relative, has_main in (
                ("go-library", False),
                ("go-main", True),
            ):
                workspace = project / relative
                workspace.mkdir()
                (workspace / "go.mod").write_text(
                    f"module example.test/{relative}\n", encoding="utf-8"
                )
                if has_main:
                    (workspace / "main.go").write_text(
                        "package main\n", encoding="utf-8"
                    )

            result = self.engine.inspect_project(project, self.contracts)

        types = {row["path"]: row["project_types"] for row in result["workspaces"]}
        self.assertEqual(
            types["fastapi-service"], ["application", "service"]
        )
        self.assertEqual(types["name-only"], [])
        self.assertEqual(types["fixture-main-library"], ["library"])
        self.assertEqual(types["root-main"], ["application"])
        self.assertEqual(types["package-main"], ["application"])
        self.assertEqual(types["go-library"], ["library"])
        self.assertEqual(types["go-main"], ["application"])

    def test_generic_python_entry_point_is_library_plugin_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "pyproject.toml").write_text(
                "[project]\n"
                "name='pytest-plugin'\n"
                "[project.entry-points.pytest11]\n"
                "plugin='pytest_plugin'\n"
                "[build-system]\n"
                "requires=['setuptools']\n"
                "build-backend='setuptools.build_meta'\n",
                encoding="utf-8",
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["project_types"], ["library"])

    def test_python_go_and_rust_markers_add_native_profiles_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            for relative in ("services/api", "services/go", "crates/cli"):
                (project / relative).mkdir(parents=True)
            (project / "services" / "api" / "pyproject.toml").write_text(
                "[project]\nname='api'\ndependencies=['django', 'fastapi']\n",
                encoding="utf-8",
            )
            (project / "services" / "go" / "go.mod").write_text(
                "module example.test/service\n", encoding="utf-8"
            )
            (project / "services" / "go" / "main.go").write_text(
                "package main\n", encoding="utf-8"
            )
            (project / "crates" / "cli" / "Cargo.toml").write_text(
                "[package]\nname='cli'\nversion='0.1.0'\n", encoding="utf-8"
            )
            (project / "crates" / "cli" / "src").mkdir()
            (project / "crates" / "cli" / "src" / "main.rs").write_text(
                "fn main() {}\n", encoding="utf-8"
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertTrue(
            {"python", "django", "fastapi", "go", "rust"}.issubset(
                result["frameworks"]
            )
        )
        self.assertTrue({"application", "service"}.issubset(result["project_types"]))
        self.assertTrue(
            {
                "python -m unittest discover",
                "go test ./...",
                "cargo test",
            }.issubset({row["command"] for row in result["commands"]})
        )

    def test_traversal_is_depth_directory_and_marker_size_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            depth_four = project / "a-one" / "two" / "three" / "four"
            depth_five = depth_four / "five"
            depth_five.mkdir(parents=True)
            (depth_four / "go.mod").write_text("module accepted\n", encoding="utf-8")
            (depth_five / "Cargo.toml").write_text(
                "[package]\nname='ignored'\n", encoding="utf-8"
            )
            bounded = project / "z-bounded"
            bounded.mkdir()
            (bounded / "pyproject.toml").write_text(
                "[project]\nname='ignored'\n", encoding="utf-8"
            )
            oversized = project / "oversized"
            oversized.mkdir()
            (oversized / "package.json").write_text(
                " " * (self.engine.MAX_MARKER_BYTES + 1), encoding="utf-8"
            )

            with mock.patch.object(self.engine, "MAX_PROJECT_DIRECTORIES", 5):
                result = self.engine.inspect_project(project, self.contracts)

        paths = {row["path"] for row in result["workspaces"]}
        self.assertIn("a-one/two/three/four", paths)
        self.assertNotIn("a-one/two/three/four/five", paths)
        self.assertNotIn("z-bounded", paths)
        self.assertNotIn("oversized", paths)
        self.assertIn("go", result["frameworks"])
        self.assertNotIn("rust", result["frameworks"])

    def test_traversal_ignores_vcs_dependency_cache_vendor_and_build_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "index.html").write_text("<main></main>", encoding="utf-8")
            for ignored in (
                ".git",
                "Node_Modules",
                "vendor",
                "cache",
                "build",
                "dist",
            ):
                directory = project / ignored / "escaped"
                directory.mkdir(parents=True)
                (directory / "pyproject.toml").write_text(
                    "[project]\nname='ignored'\n", encoding="utf-8"
                )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["frameworks"], ["static-web"])

    def test_directory_fanout_over_limit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            for name in ("a", "b", "c"):
                (project / name).mkdir()

            with mock.patch.object(
                self.engine, "MAX_DIRECTORY_ENTRIES", 2, create=True
            ):
                with self.assertRaisesRegex(
                    ValueError, r"directory entry limit exceeded: \."
                ):
                    self.engine.inspect_project(project, self.contracts)

    def test_workspace_order_breaks_casefold_ties_by_original_name(self) -> None:
        self.assertTrue(hasattr(self.engine, "_directory_name_key"))
        self.assertEqual(
            self.engine._directory_name_key("ß"),
            ("ss", "ß"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            for name in ("ß", "ss"):
                workspace = project / name
                workspace.mkdir()
                (workspace / "go.mod").write_text(
                    f"module example.test/{name}\n", encoding="utf-8"
                )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(
            [row["path"] for row in result["workspaces"]],
            [".", "ss", "ß"],
        )

    def test_oversized_lockfile_is_not_package_manager_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "package.json").write_text(
                json.dumps({"scripts": {"test": "never execute this"}}),
                encoding="utf-8",
            )
            (project / "pnpm-lock.yaml").write_text(
                " " * (self.engine.MAX_MARKER_BYTES + 1), encoding="utf-8"
            )

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["package_managers"], [])
        self.assertEqual(result["commands"], [])
        self.assertEqual(result["package_manager_conflicts"], [])

    def test_path_detectors_distinguish_files_from_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = pathlib.Path(temporary)
            (project / "index.html").mkdir()
            (project / "docs").write_text("not a directory", encoding="utf-8")

            result = self.engine.inspect_project(project, self.contracts)

        self.assertEqual(result["frameworks"], ["generic"])


class ImpactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_engine()
        self.contracts = self.engine.load_contracts(COMPANY)

    def test_skill_change_expands_to_transitive_public_surfaces(self) -> None:
        result = self.engine.calculate_impact(
            ["plugins/core-pack/skills/test-driven-development/SKILL.md"],
            self.contracts,
        )

        self.assertEqual(result["changed_paths"], [
            "plugins/core-pack/skills/test-driven-development/SKILL.md"
        ])
        self.assertTrue(
            {
                "catalog",
                "documentation",
                "evaluation",
                "marketplace-validation",
                "public-site",
                "release-validation",
                "wiki",
            }.issubset(result["effects"])
        )
        self.assertIn("python scripts/catalog.py --check", result["checks"])
        self.assertIn("python evals/run.py --check", result["checks"])

    def test_ui_change_requires_accessibility_and_browser_evidence(self) -> None:
        result = self.engine.calculate_impact(["site/index.html"], self.contracts)
        self.assertIn("accessibility", result["effects"])
        self.assertIn("browser-testing", result["effects"])
        self.assertIn("python -m unittest tests.test_site_markup -v", result["checks"])

    def test_pages_crawl_surfaces_require_public_site_and_release_checks(self) -> None:
        result = self.engine.calculate_impact(
            ["docs/robots.txt", "docs/sitemap.xml", "site/robots.txt"],
            self.contracts,
        )
        self.assertEqual(result["unclassified_paths"], [])
        self.assertIn("public-site", result["effects"])
        self.assertIn("release-validation", result["effects"])

    def test_validation_and_workflow_changes_have_nonempty_impact(self) -> None:
        for path in ("scripts/validate.py", ".github/workflows/quality-gate.yml"):
            with self.subTest(path=path):
                result = self.engine.calculate_impact([path], self.contracts)
                self.assertTrue(result["effects"])
                self.assertTrue(result["checks"])

    def test_canonical_controllers_and_installed_commands_have_impact(self) -> None:
        for path in (
            "scripts/catalog.py",
            "scripts/hygiene.py",
            "plugins/sadrazam/commands/company.md",
        ):
            with self.subTest(path=path):
                result = self.engine.calculate_impact([path], self.contracts)
                self.assertTrue(result["matched_rules"])
                self.assertTrue(result["checks"])

    def test_absolute_and_parent_paths_are_rejected(self) -> None:
        for value in ("../README.md", "/etc/passwd", "C:/Windows/system.ini"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "relative"):
                    self.engine.calculate_impact([value], self.contracts)

    def test_unmatched_paths_fail_closed_and_project_os_surfaces_are_classified(self) -> None:
        result = self.engine.calculate_impact(
            [
                ".divan/project.json",
                "plugins/sadrazam/company/portable_actions.py",
                "scripts/project_os_controller.py",
                "unknown/private.bin",
            ],
            self.contracts,
        )

        self.assertEqual(result["unclassified_paths"], ["unknown/private.bin"])
        self.assertTrue(
            {
                "portable-action",
                "project-os-controller",
                "project-os-state",
            }.issubset(result["matched_rules"])
        )

    def test_adoption_drift_and_archive_surfaces_are_classified(self) -> None:
        result = self.engine.calculate_impact(
            [
                "plugins/sadrazam/company/project_lifecycle.py",
                ".divan/install-state.json",
                ".divan/archive/2026-07-24-goal-0123456789ab/archive.json",
                ".divan/evidence/goal-0123456789ab/adoption-receipt.md",
                "canary/README.md",
            ],
            self.contracts,
        )

        self.assertEqual(result["unclassified_paths"], [])
        self.assertIn("adoption-drift-lifecycle", result["matched_rules"])
        self.assertTrue(
            {"company-validation", "documentation", "release-validation"}.issubset(
                result["effects"]
            )
        )
