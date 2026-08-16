from __future__ import annotations

import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import local_ai


class LocalAiTests(unittest.TestCase):
    def test_status_returns_local_inventory(self):
        with patch.object(
            local_ai,
            "_request",
            return_value={"models": [{"name": "qwen3:8b", "size": 42}]},
        ):
            result = local_ai.status()
        self.assertTrue(result["available"])
        self.assertEqual(result["models"][0]["name"], "qwen3:8b")

    def test_draft_is_nonexecuting_and_bounded(self):
        with patch.object(
            local_ai,
            "_request",
            return_value={"message": {"content": "Plan: inspect, change, verify."}},
        ) as request:
            result = local_ai.draft("Add a local workbench")
        self.assertFalse(result["executed"])
        self.assertEqual(result["model"], "qwen3:8b")
        self.assertEqual(request.call_args.kwargs["body"]["stream"], False)

    def test_draft_rejects_oversized_prompt(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            local_ai.draft("x" * (local_ai.MAX_PROMPT_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
