from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sbom.py"
SOURCE_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def load_sbom():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("divan_sbom", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("scripts/sbom.py yuklenemedi")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        self.assertEqual(first["creationInfo"]["created"], "1970-01-01T00:00:00Z")

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
        self.assertIn("vercel-labs/agent-skills@f8a72b96", packages["react-pack"]["sourceInfo"])
        self.assertIn("anthropics/skills@fa0fa64b", packages["zanaat-pack"]["sourceInfo"])

    def test_invalid_source_commit_is_rejected(self) -> None:
        sbom = load_sbom()
        for invalid in ("main", "abc", "g" * 40, "A" * 40, "0" * 39):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                ValueError, "40 karakterlik kucuk harfli Git SHA"
            ):
                sbom.build_spdx(ROOT, "0.12.2", invalid)

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
            expected = load_sbom().build_spdx(ROOT, "0.12.2", SOURCE_COMMIT)
            self.assertEqual(decoded, expected)
            self.assertEqual(
                payload,
                (json.dumps(expected, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(),
            )


if __name__ == "__main__":
    unittest.main()
