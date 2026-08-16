from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"

PRODUCTION_CSP = {
    "default-src": "'self'",
    "base-uri": "'none'",
    "form-action": "'none'",
    "frame-ancestors": "'none'",
    "object-src": "'none'",
    "script-src": "'self'",
    "style-src": "'self'",
    "connect-src": "ipc: http://ipc.localhost",
}

DEVELOPMENT_CSP = {
    **PRODUCTION_CSP,
    "script-src": "'self' 'unsafe-inline'",
    "style-src": "'self' 'unsafe-inline'",
    "connect-src": "ipc: http://ipc.localhost ws://localhost:1420 ws://localhost:1421",
}


class DesktopSecurityConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.security = self.config["app"]["security"]

    def test_production_csp_only_allows_bundle_and_tauri_ipc(self) -> None:
        self.assertEqual(self.security["csp"], PRODUCTION_CSP)

    def test_development_csp_limits_hmr_to_localhost(self) -> None:
        self.assertEqual(self.security["devCsp"], DEVELOPMENT_CSP)

    def test_csp_never_contains_broad_or_script_execution_relaxations(self) -> None:
        for name in ("csp", "devCsp"):
            with self.subTest(name=name):
                value = self.security[name]
                rendered = " ".join(value.values())
                self.assertNotIn("*", rendered)
                self.assertNotIn("unsafe-eval", rendered)
                self.assertNotIn("https:", rendered)
                self.assertNotIn("http://127.0.0.1:11434", rendered)


if __name__ == "__main__":
    unittest.main()
