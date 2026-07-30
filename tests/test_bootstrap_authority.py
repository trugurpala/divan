from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bootstrap_contract  # noqa: E402
import host_lifecycle  # noqa: E402
import host_profiles  # noqa: E402


def _contracts() -> tuple[dict[str, object], dict[str, object]]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    raw = (ROOT / ".agents" / "plugins" / "marketplace.json").read_bytes()
    marketplace = json.loads(raw)
    packages = {}
    for row in marketplace["plugins"]:
        package = ROOT / row["source"]["path"]
        packages[row["name"]] = {
            "skills": sorted(
                path.parent.name
                for path in (package / "skills").glob("*/SKILL.md")
            ),
            "version": row["version"],
        }
    identity = {
        "schema_version": 1,
        "source_commit": "a" * 40,
        "source_ref": f"v{version}",
        "source_repository": bootstrap_contract.CANONICAL_SOURCE,
        "version": version,
    }
    catalog = {
        "marketplace_digest": hashlib.sha256(raw).hexdigest(),
        "packages": packages,
        "schema_version": 1,
        "skill_count": 41,
        "version": version,
    }
    return identity, catalog


class BootstrapAuthorityTests(unittest.TestCase):
    def _root(
        self,
        base: pathlib.Path,
        identity: dict[str, object],
        catalog: dict[str, object],
    ) -> pathlib.Path:
        root = base / "bundle"
        root.mkdir()
        (root / "divan-bootstrap-source.json").write_text(
            json.dumps(identity), encoding="utf-8"
        )
        (root / "divan-bootstrap-catalog.json").write_text(
            json.dumps(catalog), encoding="utf-8"
        )
        return root

    def test_native_target_uses_bundled_commit_without_treating_bundle_as_git(self) -> None:
        identity, catalog = _contracts()
        with tempfile.TemporaryDirectory(prefix="divan-authority-") as temporary:
            root = self._root(pathlib.Path(temporary), identity, catalog)

            def forbidden_runner(command: list[str]):  # type: ignore[no-untyped-def]
                self.fail(f"bundled target unexpectedly executed: {command}")

            _, target = host_lifecycle._install_target(
                root,
                catalog["packages"],  # type: ignore[arg-type]
                type(
                    "Options",
                    (),
                    {
                        "source": identity["source_repository"],
                        "ref": identity["source_ref"],
                    },
                )(),
                forbidden_runner,
            )

        self.assertEqual(target["commit"], identity["source_commit"])
        self.assertEqual(target["catalog_digest"], catalog["marketplace_digest"])
        self.assertEqual(target["source"], bootstrap_contract.CANONICAL_SOURCE)

    def test_malformed_bundled_catalog_fails_closed(self) -> None:
        identity, catalog = _contracts()
        broken = json.loads(json.dumps(catalog))
        broken["packages"]["sadrazam"]["skills"] = "not-a-list"
        with tempfile.TemporaryDirectory(prefix="divan-authority-") as temporary:
            root = self._root(pathlib.Path(temporary), identity, broken)
            with self.assertRaises(host_lifecycle.InstallError):
                host_lifecycle._expected_packages(root)

    def test_recovery_and_fallback_removal_keep_the_original_pyz_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan authority ") as temporary:
            bootstrap = pathlib.Path(temporary) / "Divan Bootstrap.pyz"
            bootstrap.write_bytes(b"fixture")
            transaction = pathlib.Path(temporary) / "install journal.json"
            previous = getattr(sys, "_divan_bootstrap_path", None)
            sys._divan_bootstrap_path = str(bootstrap)
            try:
                recovery = host_profiles.recovery_command(transaction)
                rollback = host_profiles.rollback_command(pathlib.Path(temporary))
            finally:
                if previous is None:
                    del sys._divan_bootstrap_path
                else:
                    sys._divan_bootstrap_path = previous

        self.assertEqual(recovery, [sys.executable, str(bootstrap), "recover", str(transaction)])
        self.assertEqual(rollback, [sys.executable, str(bootstrap), "_fallback-remove"])


if __name__ == "__main__":
    unittest.main()
