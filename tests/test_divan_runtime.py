from __future__ import annotations

import importlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
LEGACY = PLUGIN_ROOT / "company"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import governance, kernel  # noqa: E402

from scripts import build_project_runner  # noqa: E402


class DivanRuntimeContractTests(unittest.TestCase):
    def _runtime_fixture(self) -> pathlib.Path:
        temporary = tempfile.TemporaryDirectory(prefix="divan-runtime-")
        self.addCleanup(temporary.cleanup)
        directory = pathlib.Path(temporary.name) / "divan_runtime"
        shutil.copytree(RUNTIME, directory)
        return directory

    def _contract(self, directory: pathlib.Path, name: str) -> dict[str, Any]:
        return json.loads((directory / name).read_text(encoding="utf-8"))

    def _write_contract(
        self, directory: pathlib.Path, name: str, value: dict[str, Any]
    ) -> None:
        (directory / name).write_text(
            json.dumps(value, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def test_architecture_is_single_product_and_owner_first(self) -> None:
        architecture = kernel.load_architecture(RUNTIME)

        self.assertEqual(architecture["product"]["id"], "divan")
        self.assertEqual(architecture["governance_model"]["tr"], "Divan Nizamı")
        self.assertEqual(architecture["module_count"], 9)
        self.assertEqual(
            [row["id"] for row in architecture["modules"]],
            [
                "kernel",
                "governance",
                "council",
                "evidence",
                "project",
                "records",
                "providers",
                "release",
                "api",
            ],
        )
        self.assertEqual(
            next(
                row["python_modules"]
                for row in architecture["modules"]
                if row["id"] == "evidence"
            ),
            ["receipts", "execution"],
        )
        self.assertIn(
            "compatibility",
            next(
                row["python_modules"]
                for row in architecture["modules"]
                if row["id"] == "api"
            ),
        )
        records = next(
            row
            for row in architecture["modules"]
            if row["id"] == "records"
        )
        self.assertIn("adoption_proof", records["python_modules"])
        self.assertIn("clean_room_adoption", records["capabilities"])
        self.assertEqual(
            [row["id"] for row in architecture["authority_chain"]],
            [
                "owner",
                "mandate",
                "orchestrator",
                "council",
                "specialist",
                "provider",
            ],
        )
        self.assertEqual(architecture["authority_chain"][0]["tr"], "Hükümdar")
        self.assertTrue(governance.may_expand_scope("owner", RUNTIME))
        self.assertFalse(governance.may_expand_scope("orchestrator", RUNTIME))
        self.assertIn(
            "core_has_no_external_runtime_dependency",
            architecture["invariants"],
        )

    def test_module_graph_is_acyclic_and_fail_closed(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        for row in modules["modules"]:
            if row["id"] == "council":
                row["depends_on"].append("api")
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "acyclic"):
            kernel.load_architecture(directory)

    def test_undeclared_runtime_python_file_is_rejected(self) -> None:
        directory = self._runtime_fixture()
        (directory / "undeclared.py").write_text("", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "undeclared: undeclared"):
            kernel.load_architecture(directory)

    def test_nested_runtime_python_file_is_rejected(self) -> None:
        directory = self._runtime_fixture()
        nested = directory / "unowned"
        nested.mkdir()
        (nested / "escape.py").write_text("import requests\n", encoding="utf-8")

        with self.assertRaisesRegex(
            ValueError, "must be top-level: unowned/escape.py"
        ):
            kernel.load_architecture(directory)

    def test_runtime_python_file_cannot_be_owned_twice(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        modules["modules"][1]["python_modules"].append("kernel")
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "assigned more than once: kernel"):
            kernel.load_architecture(directory)

    def test_external_runtime_dependency_is_rejected(self) -> None:
        directory = self._runtime_fixture()
        engine = directory / "engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8") + "\nimport requests\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "external dependencies: requests"):
            kernel.load_architecture(directory)

    def test_dynamic_external_runtime_dependency_is_rejected(self) -> None:
        variants = (
            '__import__("requests")',
            'import importlib\nimportlib.import_module("requests")',
            'from importlib import import_module as load\nload("requests")',
            'from builtins import __import__ as load\nload("requests")',
        )
        for source in variants:
            with self.subTest(source=source):
                directory = self._runtime_fixture()
                engine = directory / "engine.py"
                engine.write_text(
                    engine.read_text(encoding="utf-8") + f"\n{source}\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    ValueError, "external dependencies: requests"
                ):
                    kernel.load_architecture(directory)

    def test_unbounded_dynamic_runtime_import_is_rejected(self) -> None:
        directory = self._runtime_fixture()
        engine = directory / "engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8")
            + '\nmodule_name = "requests"\n__import__(module_name)\n',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "unbounded dynamic import"):
            kernel.load_architecture(directory)

    def test_real_import_requires_declared_module_dependency(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        for row in modules["modules"]:
            if row["id"] == "project":
                row["depends_on"].remove("evidence")
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(
            ValueError,
            "project must declare dependency on evidence.*project_os->receipts",
        ):
            kernel.load_architecture(directory)

    def test_schema_and_rank_booleans_are_rejected(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        modules["schema_version"] = True
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "schema version 1"):
            kernel.load_architecture(directory)

        directory = self._runtime_fixture()
        governance_contract = self._contract(directory, "governance.json")
        governance_contract["schema_version"] = True
        self._write_contract(directory, "governance.json", governance_contract)

        with self.assertRaisesRegex(ValueError, "schema version 1"):
            kernel.load_architecture(directory)

        directory = self._runtime_fixture()
        governance_contract = self._contract(directory, "governance.json")
        governance_contract["authority_chain"][1]["rank"] = True
        self._write_contract(directory, "governance.json", governance_contract)

        with self.assertRaisesRegex(ValueError, "order or identity"):
            kernel.load_architecture(directory)

    def test_bilingual_labels_must_be_non_empty_and_trimmed(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        modules["modules"][2]["tr"] = " Divan "
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "tr label.*trimmed"):
            kernel.load_architecture(directory)

        directory = self._runtime_fixture()
        governance_contract = self._contract(directory, "governance.json")
        governance_contract["product"]["en"] = ""
        self._write_contract(directory, "governance.json", governance_contract)

        with self.assertRaisesRegex(ValueError, "product en label.*trimmed"):
            kernel.load_architecture(directory)

    def test_all_canonical_modules_are_required(self) -> None:
        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        modules["modules"][5]["required"] = False
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "modules must be required"):
            kernel.load_architecture(directory)

        directory = self._runtime_fixture()
        modules = self._contract(directory, "modules.json")
        modules["modules"].pop()
        self._write_contract(directory, "modules.json", modules)

        with self.assertRaisesRegex(ValueError, "canonical nine"):
            kernel.load_architecture(directory)

    def test_runtime_python_symlink_or_out_of_root_target_is_rejected(self) -> None:
        directory = self._runtime_fixture()
        outside = directory.parent / "outside.py"
        outside.write_text("", encoding="utf-8")
        engine = directory / "engine.py"
        engine.unlink()
        try:
            os.symlink(outside, engine)
        except OSError as error:
            self.skipTest(f"symlink creation is unavailable: {error}")

        with self.assertRaisesRegex(ValueError, "symlink or reparse point"):
            kernel.load_architecture(directory)

    def test_runner_python_inventory_is_derived_from_module_contract(self) -> None:
        architecture = kernel.load_architecture(RUNTIME)
        expected_python = {
            "__init__.py",
            *{
                f"{module_name}.py"
                for row in architecture["modules"]
                for module_name in row["python_modules"]
            },
        }
        inventory = set(build_project_runner.runtime_files(RUNTIME))

        self.assertEqual(
            {name for name in inventory if name.endswith(".py")},
            expected_python,
        )
        self.assertEqual(
            {name for name in inventory if not name.endswith(".py")},
            set(kernel.RUNTIME_DATA_FILES),
        )

    def test_legacy_contract_json_is_byte_identical(self) -> None:
        for name in (
            "frameworks.json",
            "impact-graph.json",
            "roles.json",
            "workflows.json",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    (LEGACY / name).read_bytes(),
                    (RUNTIME / name).read_bytes(),
                )

    def test_legacy_python_import_aliases_canonical_module(self) -> None:
        canonical = importlib.import_module("divan_runtime.engine")
        legacy = importlib.import_module("company.engine")

        self.assertIs(legacy, canonical)

    def test_canonical_and_legacy_clis_return_the_same_contract(self) -> None:
        outputs = []
        for path in (RUNTIME / "cli.py", LEGACY / "cli.py"):
            completed = subprocess.run(
                [sys.executable, str(path), "validate", "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            outputs.append(json.loads(completed.stdout))

        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0]["product"]["id"], "divan")


if __name__ == "__main__":
    unittest.main()
