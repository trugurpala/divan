from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_update_feed.py"
SPEC = importlib.util.spec_from_file_location("desktop_update_feed", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

UpdateFeedError = MODULE.UpdateFeedError
build_feed = MODULE.build_feed
generate = MODULE.generate
validate_feed = MODULE.validate_feed


class DesktopUpdateFeedTests(unittest.TestCase):
    def test_generate_binds_feed_to_exact_installer_signature_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            installer = root / "Divan_1.3.8_x64-setup.exe"
            signature = root / "Divan_1.3.8_x64-setup.exe.sig"
            output = root / "latest.json"
            manifest = root / "divan-update-manifest.json"
            installer.write_bytes(b"signed-installer-bytes")
            signature.write_text("tauri-signature-value\n", encoding="utf-8")

            feed, evidence = generate(
                installer=installer,
                signature_path=signature,
                version="1.3.8",
                artifact_base_url="https://updates.example.test/divan",
                source_commit="a" * 40,
                source_tree="b" * 40,
                output=output,
                manifest=manifest,
                pub_date="2026-08-07T16:00:00Z",
                notes="Divan stable candidate",
            )

            windows = feed["platforms"]["windows-x86_64"]
            self.assertEqual(windows["signature"], "tauri-signature-value")
            self.assertEqual(
                windows["url"],
                "https://updates.example.test/divan/Divan_1.3.8_x64-setup.exe",
            )
            self.assertEqual(evidence["source_commit"], "a" * 40)
            self.assertEqual(evidence["source_tree"], "b" * 40)
            self.assertEqual(
                evidence["installer"]["sha256"],
                hashlib.sha256(b"signed-installer-bytes").hexdigest(),
            )
            self.assertEqual(
                evidence["feed"]["sha256"],
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), feed)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), evidence)

    def test_validate_feed_rejects_signature_url_or_version_mismatch(self) -> None:
        def candidate() -> dict[str, Any]:
            return build_feed(
                version="1.3.8",
                installer_name="Divan_1.3.8_x64-setup.exe",
                artifact_base_url="https://updates.example.test/divan/",
                signature="expected-signature",
                pub_date="2026-08-07T16:00:00Z",
            )

        feed = candidate()
        feed["platforms"]["windows-x86_64"]["signature"] = "tampered"
        with self.assertRaisesRegex(UpdateFeedError, "signature"):
            validate_feed(
                feed,
                version="1.3.8",
                installer_name="Divan_1.3.8_x64-setup.exe",
                artifact_base_url="https://updates.example.test/divan/",
                signature="expected-signature",
            )

        feed = candidate()
        feed["platforms"]["windows-x86_64"]["url"] = (
            "https://updates.example.test/divan/Divan_1.3.9_x64-setup.exe"
        )
        with self.assertRaisesRegex(UpdateFeedError, "URL"):
            validate_feed(
                feed,
                version="1.3.8",
                installer_name="Divan_1.3.8_x64-setup.exe",
                artifact_base_url="https://updates.example.test/divan/",
                signature="expected-signature",
            )

        feed = candidate()
        feed["version"] = "1.3.9"
        with self.assertRaisesRegex(UpdateFeedError, "version"):
            validate_feed(
                feed,
                version="1.3.8",
                installer_name="Divan_1.3.8_x64-setup.exe",
                artifact_base_url="https://updates.example.test/divan/",
                signature="expected-signature",
            )

    def test_rejects_non_https_or_credentialed_artifact_base(self) -> None:
        for value in (
            "http://updates.example.test/divan",
            "https://user:secret@updates.example.test/divan",
        ):
            with self.subTest(value=value):
                with self.assertRaises(UpdateFeedError):
                    build_feed(
                        version="1.3.8",
                        installer_name="Divan.exe",
                        artifact_base_url=value,
                        signature="signature",
                        pub_date="2026-08-07T16:00:00Z",
                    )

    def test_rejects_invalid_version_source_or_empty_signature(self) -> None:
        with self.assertRaisesRegex(UpdateFeedError, "SemVer"):
            build_feed(
                version="stable",
                installer_name="Divan.exe",
                artifact_base_url="https://updates.example.test/divan",
                signature="signature",
                pub_date="2026-08-07T16:00:00Z",
            )

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            installer = root / "Divan.exe"
            signature = root / "Divan.exe.sig"
            installer.write_bytes(b"installer")
            signature.write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(UpdateFeedError, "signature"):
                generate(
                    installer=installer,
                    signature_path=signature,
                    version="1.3.8",
                    artifact_base_url="https://updates.example.test/divan",
                    source_commit="not-a-commit",
                    source_tree="b" * 40,
                    output=root / "latest.json",
                    manifest=root / "manifest.json",
                )


if __name__ == "__main__":
    unittest.main()
