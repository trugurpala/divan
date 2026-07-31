from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
DIVAN = ROOT / "scripts" / "divan.py"
RUNTIME_MODULE = PLUGIN_ROOT / "divan_runtime" / "engine_registry.py"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def load_engine_registry():
    spec = importlib.util.spec_from_file_location("engine_registry_under_test", RUNTIME_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load engine registry module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALID_ENGINE = {
    "id": "lowdefy",
    "decision": "ADOPT",
    "status": "candidate",
    "license": {
        "spdx_expression": "Apache-2.0",
        "evidence": "https://github.com/lowdefy/lowdefy/blob/main/LICENSE",
    },
    "source": {
        "url": "https://github.com/lowdefy/lowdefy",
        "pin_policy": "lockfile",
    },
    "host_compatibility": ["claude", "codex", "standalone"],
    "supported_project_types": ["internal-app"],
    "forbidden_project_types": ["public-web"],
    "quality_profiles": ["internal-app-v1"],
    "installation": {
        "modes": ["provider"],
        "removal": "remove provider configuration and generated UI files",
        "rollback": "restore project-owned API and data contracts",
    },
    "escape_plan": {
        "summary": "Project data and business logic remain outside the engine.",
        "steps": ["export configuration", "remove provider", "run native tests"],
    },
    "portability": {
        "data_portable": True,
        "migration_notes": "Project-owned data stays readable without the engine.",
        "depends_on_lockfile": True,
    },
    "business_logic_ownership": {
        "owner": "project",
        "notes": "Domain behavior lives in project code.",
    },
    "frontend_replaceability": {
        "replaceable": True,
        "notes": "UI can be replaced by a custom frontend.",
    },
    "when_unavailable": "fallback",
}


def registry(*engines: dict) -> dict:
    return {"schema_version": 1, "engines": list(engines)}


class EngineRegistryValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-engines-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)

    def write_registry(self, value: object, name: str = "registry.json") -> pathlib.Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return path

    def run_cli(self, path: pathlib.Path) -> tuple[int, dict]:
        completed = subprocess.run(
            [sys.executable, str(DIVAN), "engines", "validate", "--registry", str(path), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        payload = json.loads(completed.stdout)
        return completed.returncode, payload

    def test_valid_registry_cli_is_stable_and_read_only(self) -> None:
        path = self.write_registry(registry(copy.deepcopy(VALID_ENGINE)))
        before = path.read_bytes()

        first_code, first = self.run_cli(path)
        second_code, second = self.run_cli(path)

        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first, second)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(first["command"], "engines validate")
        self.assertEqual(first["status"], "valid")
        self.assertEqual(first["engine_count"], 1)
        self.assertEqual(first["errors"], [])

    def test_human_output_reports_valid_registry(self) -> None:
        path = self.write_registry(registry(copy.deepcopy(VALID_ENGINE)))
        completed = subprocess.run(
            [sys.executable, str(DIVAN), "engines", "validate", "--registry", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Engine registry: valid", completed.stdout)

    def test_fixture_error_cases_return_stable_codes(self) -> None:
        cases = {
            "duplicate-id": (lambda data: data["engines"].append(copy.deepcopy(data["engines"][0])), "ENGINE_DUPLICATE_ID"),
            "unknown-top": (lambda data: data.update({"extra": True}), "REGISTRY_UNKNOWN_FIELD"),
            "unknown-engine": (lambda data: data["engines"][0].update({"extra": True}), "ENGINE_UNKNOWN_FIELD"),
            "invalid-id": (lambda data: data["engines"][0].update({"id": "Bad ID"}), "ENGINE_ID_INVALID"),
            "invalid-license": (lambda data: data["engines"][0]["license"].update({"spdx_expression": "not a license!"}), "ENGINE_LICENSE_INVALID"),
            "missing-license-evidence": (lambda data: data["engines"][0]["license"].pop("evidence"), "ENGINE_LICENSE_EVIDENCE_REQUIRED"),
            "missing-source-pin": (lambda data: (data["engines"][0].update({"status": "accepted"}), data["engines"][0]["source"].pop("pin", None)), "ENGINE_PIN_REQUIRED"),
            "fork-without-url": (lambda data: data["engines"][0].update({"decision": "FORK"}), "ENGINE_FORK_URL_REQUIRED"),
            "fork-same-url": (lambda data: data["engines"][0].update({"decision": "FORK", "fork_repository": data["engines"][0]["source"]["url"]}), "ENGINE_FORK_URL_INVALID"),
            "missing-escape": (lambda data: data["engines"][0].pop("escape_plan"), "ENGINE_ESCAPE_PLAN_REQUIRED"),
            "invalid-escape-type": (lambda data: data["engines"][0].update({"escape_plan": {"summary": "", "steps": "nope"}}), "ENGINE_ESCAPE_PLAN_INVALID"),
            "contradictory-portability": (lambda data: data["engines"][0]["portability"].update({"data_portable": False}), "ENGINE_PORTABILITY_CONTRADICTION"),
        }
        for name, (mutate, expected_code) in cases.items():
            with self.subTest(name=name):
                value = registry(copy.deepcopy(VALID_ENGINE))
                mutate(value)
                path = self.write_registry(value, f"{name}.json")
                before = path.read_bytes()

                code, payload = self.run_cli(path)

                self.assertEqual(code, 1)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(payload["status"], "invalid")
                codes = [error["code"] for error in payload["errors"]]
                self.assertIn(expected_code, codes)
                self.assertEqual(payload["errors"], sorted(payload["errors"], key=lambda row: (row["path"], row["code"], row["message"])))

    def test_malformed_json_invalid_utf8_and_missing_file(self) -> None:
        malformed = self.root / "broken.json"
        malformed.write_text("{", encoding="utf-8")
        invalid_utf8 = self.root / "invalid-utf8.json"
        invalid_utf8.write_bytes(b"\xff")
        missing = self.root / "missing.json"

        malformed_code, malformed_payload = self.run_cli(malformed)
        utf8_code, utf8_payload = self.run_cli(invalid_utf8)
        missing_code, missing_payload = self.run_cli(missing)

        self.assertEqual(malformed_code, 1)
        self.assertEqual(malformed_payload["errors"][0]["code"], "REGISTRY_INVALID_JSON")
        self.assertEqual(utf8_code, 2)
        self.assertEqual(utf8_payload["errors"][0]["code"], "REGISTRY_INVALID_UTF8")
        self.assertEqual(missing_code, 2)
        self.assertEqual(missing_payload["errors"][0]["code"], "REGISTRY_FILE_NOT_FOUND")

    def test_non_object_root_and_missing_engines(self) -> None:
        for value, expected_code in (([], "REGISTRY_ROOT_INVALID"), ({"schema_version": 1}, "ENGINES_REQUIRED")):
            with self.subTest(expected_code=expected_code):
                path = self.write_registry(value, f"{expected_code}.json")
                code, payload = self.run_cli(path)
                self.assertEqual(code, 1)
                self.assertEqual(payload["errors"][0]["code"], expected_code)

    def test_validator_has_no_network_imports(self) -> None:
        source = RUNTIME_MODULE.read_text(encoding="utf-8")

        self.assertNotRegex(source, r"\b(socket|urllib|http\.client|requests)\b")

    def test_example_registry_is_valid(self) -> None:
        code, payload = self.run_cli(ROOT / "registry" / "engines.example.json")

        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["engine_count"], 3)


if __name__ == "__main__":
    unittest.main()
