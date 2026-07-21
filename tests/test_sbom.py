from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sbom.py"


def git_output(root: pathlib.Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *arguments],
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=15,
    ).strip()


SOURCE_COMMIT = git_output(ROOT, "rev-parse", "HEAD")


def load_sbom():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("divan_sbom", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("scripts/sbom.py yuklenemedi")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_sbom_fixture(destination: pathlib.Path) -> None:
    for relative in (
        "release-manifest.json",
        "THIRD_PARTY_LICENSES.md",
        "registry/upstream-baselines.json",
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    for package in ("core-pack", "react-pack", "sadrazam", "ui-pack", "zanaat-pack"):
        relative = pathlib.Path("plugins") / package / ".claude-plugin" / "plugin.json"
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


class SbomTests(unittest.TestCase):
    def test_spdx_document_has_deterministic_identity_and_order(self) -> None:
        sbom = load_sbom()
        first = sbom.build_spdx(ROOT, "0.12.2", SOURCE_COMMIT)
        second = sbom.build_spdx(ROOT, "0.12.2", SOURCE_COMMIT)

        self.assertEqual(first, second)
        self.assertEqual(first["spdxVersion"], "SPDX-2.3")
        self.assertEqual(first["dataLicense"], "CC0-1.0")
        self.assertEqual(first["SPDXID"], "SPDXRef-DOCUMENT")
        self.assertEqual(
            first["documentNamespace"],
            f"https://spdx.org/spdxdocs/divan-0.12.2-{SOURCE_COMMIT}",
        )
        self.assertEqual(first["name"], "Divan-v0.12.2")
        self.assertNotIn(str(ROOT), json.dumps(first, ensure_ascii=False))
        self.assertRegex(first["creationInfo"]["created"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_creation_time_is_known_commit_time_normalized_to_utc(self) -> None:
        sbom = load_sbom()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            copy_sbom_fixture(root)
            subprocess.run(
                ["git", "-C", str(root), "init", "--quiet"],
                check=True,
                timeout=15,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "core.autocrlf", "false"],
                check=True,
                timeout=15,
            )
            subprocess.run(
                ["git", "-C", str(root), "add", "."],
                check=True,
                timeout=15,
            )
            environment = dict(os.environ)
            environment.update(
                {
                    "GIT_AUTHOR_DATE": "2030-02-03T04:05:06+05:30",
                    "GIT_COMMITTER_DATE": "2030-02-03T04:05:06+05:30",
                }
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=Divan Test",
                    "-c",
                    "user.email=divan-test@example.invalid",
                    "commit",
                    "--quiet",
                    "-m",
                    "fixture",
                ],
                check=True,
                env=environment,
                timeout=15,
            )
            source_commit = git_output(root, "rev-parse", "HEAD")

            document = sbom.build_spdx(root, "0.12.2", source_commit)

        self.assertEqual(document["creationInfo"]["created"], "2030-02-02T22:35:06Z")
        self.assertNotIn(str(root), json.dumps(document, ensure_ascii=False))

    def test_spdx_describes_exactly_the_five_marketplace_packages(self) -> None:
        sbom = load_sbom()
        document = sbom.build_spdx(ROOT, "0.12.2", SOURCE_COMMIT)
        packages = document["packages"]

        self.assertEqual(
            [package["name"] for package in packages],
            ["core-pack", "react-pack", "sadrazam", "ui-pack", "zanaat-pack"],
        )
        self.assertEqual(len(packages), 5)
        self.assertEqual(
            document["documentDescribes"],
            [package["SPDXID"] for package in packages],
        )
        self.assertEqual(
            document["relationships"],
            [
                {
                    "spdxElementId": "SPDXRef-DOCUMENT",
                    "relationshipType": "DESCRIBES",
                    "relatedSpdxElement": package["SPDXID"],
                }
                for package in packages
            ],
        )

    def test_packages_carry_license_and_pinned_source_provenance(self) -> None:
        sbom = load_sbom()
        packages = {
            package["name"]: package
            for package in sbom.build_spdx(ROOT, "0.12.2", SOURCE_COMMIT)["packages"]
        }

        self.assertEqual(packages["sadrazam"]["licenseDeclared"], "MIT")
        self.assertEqual(packages["core-pack"]["licenseDeclared"], "MIT AND CC0-1.0")
        self.assertEqual(packages["ui-pack"]["licenseDeclared"], "Apache-2.0 AND MIT")
        self.assertEqual(packages["react-pack"]["licenseDeclared"], "MIT")
        self.assertEqual(packages["zanaat-pack"]["licenseDeclared"], "Apache-2.0")
        for package in packages.values():
            self.assertEqual(package["licenseConcluded"], package["licenseDeclared"])
            self.assertFalse(package["filesAnalyzed"])
            self.assertIn(SOURCE_COMMIT, package["downloadLocation"])
            self.assertIn("THIRD_PARTY_LICENSES.md", package["sourceInfo"])
            self.assertIn("registry/upstream-baselines.json", package["sourceInfo"])
            self.assertEqual(package["versionInfo"], next(
                item["version"]
                for item in json.loads(
                    (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
                )["plugins"]
                if item["name"] == package["name"]
            ))
        self.assertIn("obra/superpowers@d884ae04", packages["core-pack"]["sourceInfo"])
        self.assertIn(
            "PatrickJS/awesome-cursorrules@b044f956f021b6e8877f16781bcfc466a6a120e9",
            packages["core-pack"]["sourceInfo"],
        )
        self.assertIn(
            "muratcankoylan/Agent-Skills-for-Context-Engineering@"
            "c578e85e40fe2bda7c1fec91ff64cf5285434934",
            packages["core-pack"]["sourceInfo"],
        )
        self.assertIn("vercel-labs/agent-skills@f8a72b96", packages["react-pack"]["sourceInfo"])
        self.assertIn("anthropics/skills@fa0fa64b", packages["zanaat-pack"]["sourceInfo"])

    def test_invalid_source_commit_is_rejected(self) -> None:
        sbom = load_sbom()
        for invalid in ("main", "abc", "g" * 40, "A" * 40, "0" * 39):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                ValueError, "40 karakterlik kucuk harfli Git SHA"
            ):
                sbom.build_spdx(ROOT, "0.12.2", invalid)

        with self.assertRaisesRegex(ValueError, "Git commit bulunamadi"):
            sbom.build_spdx(ROOT, "0.12.2", "f" * 40)

    def test_inventory_source_without_canonical_pin_fails_closed(self) -> None:
        sbom = load_sbom()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            copy_sbom_fixture(root)
            registry_path = root / "registry/upstream-baselines.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["sources"] = [
                source
                for source in registry["sources"]
                if source["repository"] != "obra/superpowers"
            ]
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "kanonik pin yok: obra/superpowers"):
                sbom.build_spdx(root, "0.12.2", SOURCE_COMMIT)

    def test_cli_writes_stable_utf8_json_with_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = pathlib.Path(temporary) / "divan.spdx.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(ROOT),
                    "--output",
                    str(output),
                    "--source-commit",
                    SOURCE_COMMIT,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = output.read_bytes()
            self.assertTrue(payload.endswith(b"\n"))
            self.assertIn("Mühürdar".encode(), payload)
            decoded = json.loads(payload.decode("utf-8"))
            version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
            expected = load_sbom().build_spdx(ROOT, version, SOURCE_COMMIT)
            self.assertEqual(decoded, expected)
            self.assertEqual(
                payload,
                (json.dumps(expected, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(),
            )


if __name__ == "__main__":
    unittest.main()
