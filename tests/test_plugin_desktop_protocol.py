from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_protocol import handle_request
from divan_runtime.execution_router import ExecutionRouter


class PluginDesktopProtocolTests(unittest.TestCase):
    def test_capabilities_advertise_read_only_plugin_inspection(self) -> None:
        response = handle_request({"command": "capabilities"}, ExecutionRouter([]))

        self.assertTrue(response["ok"], response)
        self.assertIn("plugin.inspect", response["result"]["commands"])

    def test_plugin_inspect_requires_an_explicit_manifest_path(self) -> None:
        response = handle_request({"command": "plugin.inspect"}, ExecutionRouter([]))

        self.assertFalse(response["ok"])
        self.assertEqual(
            response["error"]["code"],
            "DESKTOP_PLUGIN_MANIFEST_PATH_REQUIRED",
        )

    def test_plugin_inspect_is_read_only_and_surfaces_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            manifest = root / "plugin.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "id": "unsafe-reviewer",
                        "display_name": "Unsafe Reviewer",
                        "version": "1.0.0",
                        "api_version": 1,
                        "kind": "reviewer",
                        "transport": "sidecar-json-v1",
                        "executable": "unsafe-reviewer",
                        "capabilities": ["merge.commit"],
                        "source": {"url": "https://example.test/unsafe-reviewer"},
                        "license": {
                            "spdx_expression": "MIT",
                            "evidence": "https://example.test/LICENSE",
                        },
                        "requires_mandate": False,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            response = handle_request(
                {"command": "plugin.inspect", "manifest_path": str(manifest)},
                ExecutionRouter([]),
            )
            serialized = json.dumps(response, sort_keys=True)

        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["stage"], "invalid")
        self.assertFalse(response["result"]["activation"]["supported"])
        self.assertIn(
            "PLUGIN_CAPABILITY_RESERVED",
            {
                issue["code"]
                for issue in response["result"]["validation"]["errors"]
            },
        )
        self.assertNotIn(directory, serialized)


if __name__ == "__main__":
    unittest.main()
