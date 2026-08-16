from __future__ import annotations

import pathlib
import re
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import prompt_library


class PromptLibraryTests(unittest.TestCase):
    def test_search_returns_cc0_catalogue_results(self):
        results = prompt_library.search("linux terminal", limit=5)
        self.assertTrue(results)
        self.assertIn("id", results[0])
        self.assertEqual(prompt_library.provenance()["license"], "CC0-1.0")

    def test_catalogue_and_public_results_do_not_expose_email_addresses(self):
        email = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
        self.assertNotRegex(prompt_library.DATA_FILE.read_text(encoding="utf-8"), email)
        self.assertTrue(all(item["contributor"] == "community" for item in prompt_library.search()))

    def test_render_only_replaces_explicit_double_brace_variables(self):
        template = prompt_library.PromptTemplate(
            "demo", "Demo", "Keep {code} and replace {{name}}.", False, "TEXT", "test"
        )
        with patch("divan_runtime.prompt_library.get", return_value=template):
            result = prompt_library.render("demo", {"name": "Ottoman"})
        self.assertEqual(result["prompt"], "Keep {code} and replace Ottoman.")


if __name__ == "__main__":
    unittest.main()
