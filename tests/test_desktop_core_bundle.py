"""The sidecar must ship the runtime the contract says it ships.

PyInstaller bundles what the import graph reaches from the entry point. A
module the desktop bridge never imports is left out without a word, and the
installed product then lacks a capability the runtime contract declares. This
happened: the first sidecar built in the delivery campaign carried 59 of 93
declared modules, missing worker execution, independent review, the
verification guard and failure learning.

The build now derives its hidden imports from modules.json. These tests pin
that derivation without running PyInstaller, so they are cheap enough for every
run; a slow test that actually builds and opens the archive lives behind an
environment flag for the release path.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_desktop_core.py"
RUNTIME = ROOT / "plugins" / "sadrazam" / "divan_runtime"


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_desktop_core", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SidecarBundleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = _load_builder()
        contract = json.loads((RUNTIME / "modules.json").read_text(encoding="utf-8"))
        self.declared = {
            name for entry in contract["modules"] for name in entry["python_modules"]
        }

    def test_every_declared_module_becomes_a_hidden_import(self) -> None:
        bundled = {
            name.removeprefix("divan_runtime.")
            for name in self.builder.declared_runtime_modules()
        }
        missing = sorted(self.declared - bundled)
        self.assertEqual(missing, [], "declared but not bundled: " + ", ".join(missing))

    def test_no_undeclared_module_is_smuggled_in(self) -> None:
        bundled = {
            name.removeprefix("divan_runtime.")
            for name in self.builder.declared_runtime_modules()
        }
        extra = sorted(bundled - self.declared)
        self.assertEqual(extra, [], "bundled but never declared: " + ", ".join(extra))

    def test_hidden_import_flags_are_well_formed(self) -> None:
        flags = self.builder.hidden_import_flags()
        self.assertEqual(len(flags) % 2, 0)
        self.assertTrue(all(flags[i] == "--hidden-import" for i in range(0, len(flags), 2)))
        modules = flags[1::2]
        self.assertTrue(all(name.startswith("divan_runtime.") for name in modules))
        self.assertEqual(len(modules), len(set(modules)), "duplicate hidden imports")

    def test_the_capabilities_this_campaign_proved_are_bundled(self) -> None:
        # The ones the first sidecar silently dropped. Named so a regression
        # reads as what it is rather than as a count.
        bundled = set(self.builder.declared_runtime_modules())
        for name in (
            "divan_runtime.worker_execution",
            "divan_runtime.worker_review",
            "divan_runtime.worker_process",
            "divan_runtime.verification_guard",
            "divan_runtime.failure_learning",
            "divan_runtime.doctor",
        ):
            with self.subTest(module=name):
                self.assertIn(name, bundled)


@unittest.skipUnless(
    os.environ.get("DIVAN_SIDECAR_BUILD_CHECK") == "1",
    "set DIVAN_SIDECAR_BUILD_CHECK=1 to build the sidecar and open its archive",
)
class SidecarBundleBuildTests(unittest.TestCase):
    """Slow, real: build the binary and read the module list out of it."""

    def test_built_binary_carries_every_declared_module(self) -> None:
        import subprocess
        import sys
        import tempfile

        subprocess.run([sys.executable, str(BUILDER)], cwd=ROOT, check=True, capture_output=True)
        from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader

        exe = next((ROOT / "apps" / "desktop" / "src-tauri" / "binaries").glob("divan-core-*"))
        archive = CArchiveReader(str(exe))
        pyz_name = next(n for n in archive.toc if n.endswith(".pyz"))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pyz") as tmp:
            tmp.write(archive.extract(pyz_name))
        try:
            found = set(ZlibArchiveReader(tmp.name).toc.keys())
        finally:
            os.unlink(tmp.name)
        contract = json.loads((RUNTIME / "modules.json").read_text(encoding="utf-8"))
        declared = {
            f"divan_runtime.{n}" for e in contract["modules"] for n in e["python_modules"]
        }
        self.assertEqual(sorted(declared - found), [])


if __name__ == "__main__":
    unittest.main()
