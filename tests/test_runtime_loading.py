from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import json
import pathlib
import shutil
import stat
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "plugins" / "sadrazam" / "divan_runtime"
PLUGIN_ROOT = RUNTIME.parent
LEGACY_ALIASES = (
    "adoption",
    "cli",
    "engine",
    "goal_archive",
    "goals",
    "project_lifecycle",
    "project_os",
    "project_state",
    "project_transactions",
    "providers",
    "receipts",
)


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def cached_modules(values: dict[str, types.ModuleType]):
    previous = {name: sys.modules.get(name) for name in values}
    sys.modules.update(values)
    try:
        yield
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


@contextlib.contextmanager
def isolated_runtime_imports():
    def selected(name: str) -> bool:
        return (
            name == "_compat"
            or name in {"company", "divan_runtime"}
            or name.startswith(("company.", "divan_runtime."))
        )

    previous_path = list(sys.path)
    previous = {
        name: module for name, module in sys.modules.items() if selected(name)
    }
    for name in previous:
        sys.modules.pop(name, None)
    try:
        sys.path.insert(0, str(PLUGIN_ROOT))
        yield
    finally:
        for name in [name for name in sys.modules if selected(name)]:
            sys.modules.pop(name, None)
        sys.modules.update(previous)
        sys.path[:] = previous_path


def copy_runtime(root: pathlib.Path) -> pathlib.Path:
    destination = root / "plugins" / "sadrazam" / "divan_runtime"
    shutil.copytree(RUNTIME, destination)
    return destination


class RuntimeLoadingTests(unittest.TestCase):
    def test_repository_cli_source_binds_and_restores_cached_runtime(self) -> None:
        cli = load_module("divan_runtime_loading_cli", ROOT / "scripts" / "divan.py")
        fake_package = types.ModuleType("divan_runtime")
        fake_package.__path__ = []  # type: ignore[attr-defined]
        fake_cli = types.ModuleType("divan_runtime.cli")
        called: list[list[str]] = []

        def fake_main(arguments: list[str]) -> int:
            called.append(arguments)
            return 77

        fake_cli.main = fake_main  # type: ignore[attr-defined]
        output = io.StringIO()
        original_path = list(sys.path)
        with cached_modules(
            {"divan_runtime": fake_package, "divan_runtime.cli": fake_cli}
        ), contextlib.redirect_stdout(output):
            result = cli.main(["validate", "--json"])
            self.assertIs(sys.modules["divan_runtime"], fake_package)
            self.assertIs(sys.modules["divan_runtime.cli"], fake_cli)
            self.assertEqual(sys.path, original_path)

        self.assertEqual(result, 0)
        self.assertEqual(called, [])
        self.assertEqual(json.loads(output.getvalue())["status"], "valid")

    def test_contract_validation_ignores_fake_cached_modules(self) -> None:
        contracts = load_module(
            "divan_company_contract_loading",
            ROOT / "scripts" / "company_contracts.py",
        )
        fake_package = types.ModuleType("divan_runtime")
        fake_package.__path__ = []  # type: ignore[attr-defined]
        fake_engine = types.ModuleType("divan_runtime.engine")
        fake_kernel = types.ModuleType("divan_runtime.kernel")
        fake_engine.load_contracts = lambda _root: None  # type: ignore[attr-defined]
        fake_kernel.load_architecture = lambda _root: None  # type: ignore[attr-defined]
        with tempfile.TemporaryDirectory(prefix="divan-runtime-load-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            (runtime / "engine.py").write_text(
                "this is invalid Python !!!\n", encoding="utf-8"
            )
            original_path = list(sys.path)
            with cached_modules(
                {
                    "divan_runtime": fake_package,
                    "divan_runtime.engine": fake_engine,
                    "divan_runtime.kernel": fake_kernel,
                }
            ):
                errors = contracts.validate(root)
                self.assertIs(sys.modules["divan_runtime"], fake_package)
                self.assertIs(sys.modules["divan_runtime.engine"], fake_engine)
                self.assertIs(sys.modules["divan_runtime.kernel"], fake_kernel)
                self.assertEqual(sys.path, original_path)

        self.assertTrue(errors)
        self.assertIn("invalid syntax", errors[0].lower())

    def test_contract_validation_isolates_sequential_roots(self) -> None:
        contracts = load_module(
            "divan_company_contract_sequence",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-runtime-roots-") as temporary:
            base = pathlib.Path(temporary)
            valid_root = base / "valid"
            invalid_root = base / "invalid"
            copy_runtime(valid_root)
            invalid_runtime = copy_runtime(invalid_root)
            (invalid_runtime / "roles.json").write_text("{\n", encoding="utf-8")

            self.assertEqual(contracts.validate(valid_root), [])
            errors = contracts.validate(invalid_root)
            self.assertTrue(errors)
            self.assertIn("roles.json", errors[0])
            self.assertEqual(contracts.validate(valid_root), [])

    def test_contract_validation_rejects_linked_runtime_without_loading(self) -> None:
        contracts = load_module(
            "divan_company_contract_link",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-runtime-link-") as temporary:
            base = pathlib.Path(temporary)
            root = base / "repository"
            external_runtime = copy_runtime(base / "external")
            sibling_runtime = copy_runtime(root / "sibling")
            parent = root / "plugins" / "sadrazam"
            parent.mkdir(parents=True)
            for name, target in (
                ("external", external_runtime),
                ("sibling", sibling_runtime),
            ):
                runtime = parent / "divan_runtime"
                try:
                    runtime.symlink_to(target, target_is_directory=True)
                except OSError as error:
                    self.skipTest(f"directory symlink unavailable: {error}")
                with self.subTest(target=name), mock.patch.object(
                    contracts, "_isolated_runtime"
                ) as loader:
                    errors = contracts.validate(root)
                    self.assertTrue(errors)
                    self.assertRegex(errors[0], "symlink|reparse")
                    loader.assert_not_called()
                runtime.unlink()

    def test_contract_validation_rejects_reparse_runtime_without_loading(self) -> None:
        contracts = load_module(
            "divan_company_contract_reparse",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-runtime-reparse-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            original_lstat = pathlib.Path.lstat

            def fake_lstat(path: pathlib.Path):
                actual = original_lstat(path)
                if path == runtime:
                    return types.SimpleNamespace(
                        st_mode=actual.st_mode,
                        st_file_attributes=getattr(
                            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
                        ),
                        st_dev=actual.st_dev,
                        st_ino=actual.st_ino,
                    )
                return actual

            with mock.patch.object(
                pathlib.Path, "lstat", fake_lstat
            ), mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertRegex(errors[0], "symlink|reparse")
            loader.assert_not_called()

    def test_contract_validation_rejects_resolved_external_or_sibling_runtime(
        self,
    ) -> None:
        contracts = load_module(
            "divan_company_contract_containment",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-runtime-target-") as temporary:
            base = pathlib.Path(temporary)
            root = base / "repository"
            runtime = copy_runtime(root)
            targets = (
                ("external", copy_runtime(base / "external")),
                ("sibling", copy_runtime(root / "sibling")),
            )
            original_resolve = pathlib.Path.resolve
            for name, target in targets:
                resolved_target = original_resolve(target, strict=True)

                def fake_resolve(path: pathlib.Path, strict: bool = False):
                    if path == runtime:
                        return resolved_target
                    return original_resolve(path, strict=strict)

                with self.subTest(target=name), mock.patch.object(
                    pathlib.Path, "resolve", fake_resolve
                ), mock.patch.object(contracts, "_isolated_runtime") as loader:
                    errors = contracts.validate(root)
                    self.assertTrue(errors)
                    self.assertIn(
                        "repository root"
                        if name == "external"
                        else "canonical repository path",
                        errors[0],
                    )
                    loader.assert_not_called()

    def test_contract_validation_rejects_non_directory_without_loading(self) -> None:
        contracts = load_module(
            "divan_company_contract_file",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-runtime-file-") as temporary:
            root = pathlib.Path(temporary)
            runtime = root / "plugins" / "sadrazam" / "divan_runtime"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("not a directory\n", encoding="utf-8")

            with mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertIn("directory", errors[0])
            loader.assert_not_called()

    def test_contract_validation_rejects_linked_source_without_loading(self) -> None:
        contracts = load_module(
            "divan_company_contract_source_link",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-source-link-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            source = runtime / "engine.py"
            external = root / "external-engine.py"
            external.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            source.unlink()
            try:
                source.symlink_to(external)
            except OSError as error:
                self.skipTest(f"file symlink unavailable: {error}")

            with mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertRegex(errors[0], "symlink|reparse")
            loader.assert_not_called()

    def test_contract_validation_rejects_reparse_source_without_loading(self) -> None:
        contracts = load_module(
            "divan_company_contract_source_reparse",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-source-reparse-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            source = runtime / "engine.py"
            original_lstat = pathlib.Path.lstat

            def fake_lstat(path: pathlib.Path):
                actual = original_lstat(path)
                if path == source:
                    return types.SimpleNamespace(
                        st_mode=actual.st_mode,
                        st_file_attributes=getattr(
                            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
                        ),
                        st_dev=actual.st_dev,
                        st_ino=actual.st_ino,
                    )
                return actual

            with mock.patch.object(
                pathlib.Path, "lstat", fake_lstat
            ), mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertRegex(errors[0], "symlink|reparse")
            loader.assert_not_called()

    def test_contract_validation_rejects_resolved_external_or_sibling_source(
        self,
    ) -> None:
        contracts = load_module(
            "divan_company_contract_source_containment",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-source-target-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            source = runtime / "engine.py"
            external = root / "external-engine.py"
            external.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            targets = (("external", external), ("sibling", runtime / "kernel.py"))
            original_resolve = pathlib.Path.resolve
            for name, target in targets:
                resolved_target = original_resolve(target, strict=True)

                def fake_resolve(path: pathlib.Path, strict: bool = False):
                    if path == source:
                        return resolved_target
                    return original_resolve(path, strict=strict)

                with self.subTest(target=name), mock.patch.object(
                    pathlib.Path, "resolve", fake_resolve
                ), mock.patch.object(contracts, "_isolated_runtime") as loader:
                    errors = contracts.validate(root)
                    self.assertTrue(errors)
                    self.assertIn(
                        "runtime root"
                        if name == "external"
                        else "canonical runtime path",
                        errors[0],
                    )
                    loader.assert_not_called()

    def test_contract_validation_rejects_source_identity_change_without_loading(
        self,
    ) -> None:
        contracts = load_module(
            "divan_company_contract_source_identity",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-source-identity-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            source = runtime / "engine.py"
            original_lstat = pathlib.Path.lstat
            inspections = 0

            def fake_lstat(path: pathlib.Path):
                nonlocal inspections
                actual = original_lstat(path)
                if path != source:
                    return actual
                inspections += 1
                if inspections == 1:
                    return actual
                return types.SimpleNamespace(
                    st_mode=actual.st_mode,
                    st_file_attributes=getattr(
                        actual, "st_file_attributes", 0
                    ),
                    st_dev=actual.st_dev,
                    st_ino=actual.st_ino + 1,
                )

            with mock.patch.object(
                pathlib.Path, "lstat", fake_lstat
            ), mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertIn("changed during validation", errors[0])
            loader.assert_not_called()

    def test_contract_validation_rejects_non_regular_source_without_loading(
        self,
    ) -> None:
        contracts = load_module(
            "divan_company_contract_source_file",
            ROOT / "scripts" / "company_contracts.py",
        )
        with tempfile.TemporaryDirectory(prefix="divan-source-file-") as temporary:
            root = pathlib.Path(temporary)
            runtime = copy_runtime(root)
            source = runtime / "engine.py"
            source.unlink()
            source.mkdir()

            with mock.patch.object(contracts, "_isolated_runtime") as loader:
                errors = contracts.validate(root)

            self.assertTrue(errors)
            self.assertIn("regular file", errors[0])
            loader.assert_not_called()

    def test_legacy_compat_rebinds_spoofed_expected_paths_to_exact_source(self) -> None:
        compatibility = load_module(
            "divan_legacy_compat_loading",
            ROOT / "plugins" / "sadrazam" / "company" / "_compat.py",
        )
        fake_package = types.ModuleType("divan_runtime")
        fake_package.__file__ = str(RUNTIME / "__init__.py")
        fake_package.__path__ = [str(RUNTIME)]  # type: ignore[attr-defined]
        fake_package.compromised = True  # type: ignore[attr-defined]
        fake_engine = types.ModuleType("divan_runtime.engine")
        fake_engine.__file__ = str(RUNTIME / "engine.py")
        fake_engine.compromised = True  # type: ignore[attr-defined]

        def fake_loader(_root: pathlib.Path) -> str:
            return "ambient fake"

        fake_engine.load_contracts = fake_loader  # type: ignore[attr-defined]
        namespace = {
            "__file__": str(ROOT / "plugins" / "sadrazam" / "company" / "engine.py"),
            "__name__": "company.engine",
        }
        original_path = list(sys.path)
        with cached_modules(
            {"divan_runtime": fake_package, "divan_runtime.engine": fake_engine}
        ):
            implementation = compatibility.expose("engine", namespace)
            self.assertIs(implementation, fake_engine)
            self.assertIs(sys.modules["divan_runtime"], fake_package)
            self.assertIs(sys.modules["divan_runtime.engine"], fake_engine)
            self.assertFalse(hasattr(fake_package, "compromised"))
            self.assertFalse(hasattr(fake_engine, "compromised"))
            self.assertIsNot(fake_engine.load_contracts, fake_loader)  # type: ignore[attr-defined]
            self.assertIs(namespace["load_contracts"], fake_engine.load_contracts)  # type: ignore[attr-defined]
            self.assertEqual(
                pathlib.Path(str(fake_engine.__file__)).resolve(),  # type: ignore[attr-defined]
                RUNTIME / "engine.py",
            )
        self.assertEqual(sys.path, original_path)

    def test_every_legacy_python_alias_is_the_canonical_module(self) -> None:
        with isolated_runtime_imports():
            for name in LEGACY_ALIASES:
                with self.subTest(module=name):
                    canonical = importlib.import_module(f"divan_runtime.{name}")
                    legacy = importlib.import_module(f"company.{name}")
                    self.assertIs(legacy, canonical)
                    self.assertEqual(
                        pathlib.Path(str(legacy.__file__)).resolve(),
                        RUNTIME / f"{name}.py",
                    )


if __name__ == "__main__":
    unittest.main()
