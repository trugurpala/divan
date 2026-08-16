from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.context_compiler import (
    Detail,
    TokenConfidence,
    build_candidates,
    compile_context,
    unknown_usage_pack,
)

TASK = {
    "title": "Vaka kuyrugunda atomik sahiplenme",
    "summary": "Bir vaka ayni anda yalniz bir operatore atanabilmeli.",
    "acceptance": [
        "Iki operator ayni vakayi ayni anda alamaz.",
        "Sahiplenme denemesi kayit birakir.",
    ],
}


def candidates(**overrides):
    payload = {
        "task_contract": TASK,
        "project_contract": {"outcome": "Ekip vakalari izleyebilsin."},
        "ux_contract": {"measurable_outcomes": ["Vaka 3 tiklamada alinir."]},
        "architecture_decisions": [
            {
                "decision_id": "adr-1",
                "title": "Depolama",
                "choice": "SQLite",
                "rationale": "Tek makinede yerel calisma.",
            }
        ],
        "recalled_memory": [{"item_id": "lesson-1", "summary": "Kilit sirasi onemli."}],
        "incidents": [{"item_id": "lesson-2", "summary": "Yaris kosulu daha once oldu."}],
        "source_files": [{"path": "app/queue.py", "symbols": "def claim_case(...)"}],
        "related_tests": [{"path": "tests/test_queue.py", "symbols": "def test_claim(...)"}],
        "current_diff": "diff --git a/app/queue.py b/app/queue.py",
        "current_failure": "AssertionError: two operators claimed the same case",
    }
    payload.update(overrides)
    return build_candidates(**payload)


class ContextCompilerTests(unittest.TestCase):
    def test_the_task_and_its_failure_come_before_background_reading(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=10_000)
        keys = [item.key for item in pack.items]

        # A worker that only gets background reading will guess at the job.
        self.assertLess(keys.index("task-contract"), keys.index("adr-1"))
        self.assertLess(keys.index("current-failure"), keys.index("lesson-1"))
        self.assertLess(keys.index("acceptance"), keys.index("app/queue.py"))

    def test_a_small_budget_keeps_the_task_and_drops_the_rest_loudly(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=30)

        self.assertTrue(pack.truncated)
        self.assertTrue(pack.omitted)
        self.assertIn("task-contract", [item.key for item in pack.items])
        for omission in pack.omitted:
            self.assertTrue(omission.reason)
            self.assertGreater(omission.estimated_tokens, 0)
        self.assertIn("omitted", " ".join(pack.notes))

    def test_nothing_is_dropped_silently(self) -> None:
        everything = candidates()
        pack = compile_context("DIV-1", everything, budget_tokens=25)

        kept = {item.key for item in pack.items}
        dropped = {item.key for item in pack.omitted}
        # Every candidate is accounted for on exactly one side of the line.
        self.assertEqual(kept | dropped, {item.key for item in everything})
        self.assertFalse(kept & dropped)

    def test_a_budget_that_fits_nothing_is_reported_not_shipped(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=1)

        self.assertTrue(pack.budget_exceeded)
        self.assertEqual(pack.items, ())
        self.assertIn("no item fits", " ".join(pack.notes))

    def test_token_confidence_is_never_fabricated(self) -> None:
        estimated = compile_context("DIV-1", candidates(), budget_tokens=10_000)
        self.assertEqual(estimated.token_confidence, TokenConfidence.ESTIMATED)
        self.assertIsNone(estimated.exact_tokens)

        measured = compile_context(
            "DIV-1", candidates(), budget_tokens=10_000, exact_tokens=1234
        )
        self.assertEqual(measured.token_confidence, TokenConfidence.EXACT)
        self.assertEqual(measured.exact_tokens, 1234)

        unknown = unknown_usage_pack("DIV-1", 10_000)
        self.assertEqual(unknown.token_confidence, TokenConfidence.UNKNOWN)
        self.assertIsNone(unknown.exact_tokens)

    def test_the_pack_stays_inside_its_budget(self) -> None:
        for budget in (20, 50, 200, 10_000):
            pack = compile_context("DIV-1", candidates(), budget_tokens=budget)
            self.assertLessEqual(pack.estimated_tokens, budget, budget)

    def test_progressive_detail_levels_are_carried_through(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=10_000)
        by_key = {item.key: item for item in pack.items}

        self.assertEqual(by_key["task-contract"].detail, Detail.FULL)
        self.assertEqual(by_key["adr-1"].detail, Detail.SUMMARY)
        self.assertEqual(by_key["app/queue.py"].detail, Detail.SYMBOLS)

    def test_provenance_says_where_every_piece_came_from(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=10_000)
        provenance = pack.to_dict()["source_provenance"]

        self.assertIn("divan:task", provenance)
        self.assertIn("divan:agency-memory", provenance)
        self.assertIn("divan:spec-compiler", provenance)
        self.assertIn("divan:repo", provenance)

    def test_the_manifest_does_not_repeat_the_context_body(self) -> None:
        pack = compile_context("DIV-1", candidates(), budget_tokens=10_000)
        payload = pack.to_dict()

        self.assertTrue(all(item["text"] is None for item in payload["items"]))
        self.assertIn("yalniz bir operatore atanabilmeli", pack.render())

    def test_an_empty_or_negative_budget_is_refused(self) -> None:
        for budget in (0, -1):
            with self.assertRaises(ValueError):
                compile_context("DIV-1", candidates(), budget_tokens=budget)


if __name__ == "__main__":
    unittest.main()
