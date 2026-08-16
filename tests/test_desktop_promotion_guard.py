from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from scripts.desktop_update_feed import generate

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_promotion_guard.py"
COMMIT = "a" * 40
TREE = "b" * 40
VERSION = "1.3.8"
BASE_URL = "https://downloads.example.com/divan/desktop-v1.3.8"
ENDPOINT = "https://updates.example.com/divan/latest.json"


class DesktopPromotionGuardTests(unittest.TestCase):
    def _candidate(self, root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
        installer = root / "Ottoman_1.3.8_x64-setup.exe"
        installer.write_bytes(b"synthetic signed installer fixture")
        signature = pathlib.Path(f"{installer}.sig")
        signature.write_text("synthetic-updater-signature\n", encoding="utf-8")
        generate(
            installer=installer,
            signature_path=signature,
            version=VERSION,
            artifact_base_url=BASE_URL,
            source_commit=COMMIT,
            source_tree=TREE,
            output=root / "latest.json",
            manifest=root / "ottoman-update-manifest.json",
            pub_date="2026-08-07T21:00:00Z",
            notes="fixture",
        )
        return installer, signature

    def _run(
        self,
        root: pathlib.Path,
        *,
        commit: str = COMMIT,
        tree: str = TREE,
        base_url: str = BASE_URL,
        endpoint: str = ENDPOINT,
        checksums: pathlib.Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(root),
            "--source-commit",
            commit,
            "--source-tree",
            tree,
            "--version",
            VERSION,
            "--artifact-base-url",
            base_url,
            "--updater-endpoint",
            endpoint,
        ]
        if checksums is not None:
            command.extend(["--checksums", str(checksums)])
        return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)

    def test_valid_source_bound_candidate_passes_and_writes_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._candidate(root)
            checksums = root / "SHA256SUMS.txt"
            result = self._run(root, checksums=checksums)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["source_commit"], COMMIT)
            self.assertEqual(report["source_tree"], TREE)
            self.assertEqual(report["updater_endpoint"], ENDPOINT)
            text = checksums.read_text(encoding="utf-8")
            self.assertIn("Ottoman_1.3.8_x64-setup.exe", text)
            self.assertIn("Ottoman_1.3.8_x64-setup.exe.sig", text)
            self.assertIn("latest.json", text)
            self.assertIn("ottoman-update-manifest.json", text)

    def test_tampered_installer_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            installer, _ = self._candidate(root)
            installer.write_bytes(installer.read_bytes() + b"tamper")
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("installer SHA-256 does not match", result.stderr)

    def test_wrong_source_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._candidate(root)
            result = self._run(root, commit="c" * 40)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not bound to the exact release source", result.stderr)

    def test_wrong_artifact_base_url_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._candidate(root)
            result = self._run(root, base_url="https://other.example.com/releases")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("feed URL does not match", result.stderr)

    def test_updater_endpoint_requires_credential_free_https(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._candidate(root)
            result = self._run(root, endpoint="https://user:secret@example.com/latest.json")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not contain credentials", result.stderr)

    def test_missing_paired_signature_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            _, signature = self._candidate(root)
            signature.unlink()
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("paired with the NSIS installer is missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
