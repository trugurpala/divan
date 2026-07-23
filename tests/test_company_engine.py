import importlib.util
import json
import pathlib
import tempfile
import unittest

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
        self.assertEqual(len(contracts.workflows), 8)
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
