from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request


class DesktopProtocolTests(unittest.TestCase):
    def test_capabilities_response_has_envelope(self):
        response = handle_request({"command": "capabilities"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["api_version"], 1)
        self.assertEqual(response["result"]["product"], "Divan")

    def test_unknown_command_has_stable_error_code(self):
        response = handle_request({"command": "nope"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "DESKTOP_COMMAND_UNKNOWN")

    def test_bridge_reads_and_writes_one_json_line(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "divan-desktop-bridge.py")],
            cwd=ROOT,
            input=json.dumps({"command": "capabilities"}) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["product"], "Divan")

    def test_bridge_rejects_invalid_json(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "divan-desktop-bridge.py")],
            cwd=ROOT,
            input="{\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["error"]["code"], "DESKTOP_REQUEST_INVALID_JSON")


if __name__ == "__main__":
    unittest.main()
