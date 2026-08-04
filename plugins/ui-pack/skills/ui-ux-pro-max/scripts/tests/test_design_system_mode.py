#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for explicit light/dark intent and palette coherence."""

import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import design_system as design_system_module  # noqa: E402, I001
from design_system import (  # noqa: E402
    DesignSystemGenerator,
    _contrast_ratio,
    _color_mode_metadata,
    _filter_anti_patterns_for_mode,
    _palette_mode,
    _query_color_mode,
    _relative_luminance,
    _resolve_color_mode,
    _select_palette_for_mode,
)

LIGHT_PALETTE = {
    "Product Type": "SaaS",
    "Background": "#F8FAFC",
    "Foreground": "#020617",
}
DARK_PALETTE = {
    "Product Type": "Fintech/Crypto",
    "Background": "#0F172A",
    "Foreground": "#F8FAFC",
}
LOW_CONTRAST_DARK_PALETTE = {
    "Product Type": "Low Contrast",
    "Background": "#101010",
    "Foreground": "#111111",
}
MALFORMED_PALETTE = {
    "Product Type": "Malformed",
    "Background": "not-a-color",
    "Foreground": "#000000",
}
DARK_PRIMARY_STYLE = {
    "Style Category": "Modern Dark (Cinema Mobile)",
    "Light Mode ✓": "✓ Light mode only as exception",
    "Dark Mode ✓": "✓ Dark Mode Primary",
}
DUAL_MODE_STYLE = {
    "Style Category": "Minimalism",
    "Light Mode ✓": "✓ Full",
    "Dark Mode ✓": "✓ Full",
}


class TestColorMath(unittest.TestCase):
    def test_luminance_parses_three_and_six_digit_hex(self):
        self.assertAlmostEqual(_relative_luminance("#FFF"), 1.0, places=6)
        self.assertAlmostEqual(_relative_luminance("#000000"), 0.0, places=6)

    def test_luminance_rejects_invalid_values(self):
        for value in ("", "#12", "#GGGGGG", None):
            with self.subTest(value=value):
                self.assertIsNone(_relative_luminance(value))

    def test_palette_mode_uses_background_luminance(self):
        self.assertEqual(_palette_mode(DARK_PALETTE), "dark")
        self.assertEqual(_palette_mode(LIGHT_PALETTE), "light")
        self.assertEqual(_palette_mode({"Background": "nope"}), "unknown")

    def test_contrast_ratio_requires_two_parseable_colors(self):
        self.assertGreaterEqual(_contrast_ratio(DARK_PALETTE), 4.5)
        self.assertIsNone(_contrast_ratio({"Background": "#000000"}))


class TestIntentResolution(unittest.TestCase):
    def test_explicit_dark_markers(self):
        for query in (
            "dashboard dark mode",
            "dashboard dark theme",
            "gaming OLED",
            "gösterge koyu mod",
        ):
            with self.subTest(query=query):
                self.assertEqual(_query_color_mode(query), "dark")

    def test_explicit_light_and_negated_dark_markers(self):
        for query in (
            "dashboard light mode",
            "dashboard no dark mode",
            "avoid dark mode",
            "never use dark mode",
            "dark_mode=false",
            "not a dark theme",
            "dark mode disabled",
            "karanlık tema olmasın",
            "karanlık mod olmasın",
            "dark mode istemiyorum",
            "I don't want a dark theme",
            "koyu tema istemiyorum",
            "gösterge açık mod",
        ):
            with self.subTest(query=query):
                self.assertEqual(_query_color_mode(query), "light")

    def test_negated_light_markers_resolve_dark(self):
        for query in (
            "dashboard no light mode",
            "never use light theme",
            "light_mode=off",
            "not a light theme",
            "açık tema olmasın",
            "light mode istemiyorum",
            "I don't want light mode",
            "açık mod istemiyorum",
        ):
            with self.subTest(query=query):
                self.assertEqual(_query_color_mode(query), "dark")

    def test_conflicting_explicit_markers_fail_closed(self):
        self.assertEqual(
            _query_color_mode("support both dark mode and light mode"), "conflict"
        )

    def test_neutral_query_is_auto(self):
        self.assertEqual(_query_color_mode("healthcare booking app"), "auto")

    def test_neutral_fixture_set_stays_automatic(self):
        original_anti_pattern = "Complex jargon + Tiny tap targets"
        for query in (
            "saas dashboard",
            "clinic booking",
            "portfolio",
            "ecommerce",
            "banking",
            "education",
            "news",
            "travel",
            "analytics",
            "crm",
        ):
            with self.subTest(query=query):
                decision = _resolve_color_mode(query, DUAL_MODE_STYLE)
                chosen, matched = _select_palette_for_mode(
                    [LIGHT_PALETTE, DARK_PALETTE], decision["requested"]
                )
                filtered = _filter_anti_patterns_for_mode(
                    original_anti_pattern, decision["requested"]
                )
                self.assertEqual(decision["requested"], "auto")
                self.assertIs(chosen, LIGHT_PALETTE)
                self.assertTrue(matched)
                self.assertEqual(filtered, original_anti_pattern)

    def test_explicit_light_overrides_dark_primary_style(self):
        decision = _resolve_color_mode("cinema app light mode", DARK_PRIMARY_STYLE)
        self.assertEqual(decision["requested"], "light")
        self.assertEqual(decision["source"], "query")

    def test_dark_primary_style_is_fallback_for_neutral_query(self):
        decision = _resolve_color_mode("cinema app", DARK_PRIMARY_STYLE)
        self.assertEqual(decision["requested"], "dark")
        self.assertEqual(decision["source"], "style")

    def test_dark_only_support_flags_are_detected(self):
        decision = _resolve_color_mode(
            "developer tool",
            {"Light Mode ✓": "✗ No", "Dark Mode ✓": "✓ Only"},
        )
        self.assertEqual(decision["requested"], "dark")
        self.assertEqual(decision["source"], "style")

    def test_dual_mode_style_keeps_neutral_behavior_automatic(self):
        decision = _resolve_color_mode("healthcare booking app", DUAL_MODE_STYLE)
        self.assertEqual(decision["requested"], "auto")
        self.assertEqual(decision["source"], "default")

    def test_empty_style_keeps_neutral_behavior_automatic(self):
        self.assertEqual(
            _resolve_color_mode("healthcare booking app", {}),
            {"requested": "auto", "source": "default"},
        )


class TestPaletteSelection(unittest.TestCase):
    def test_dark_mode_skips_light_palette(self):
        chosen, matched = _select_palette_for_mode(
            [LIGHT_PALETTE, DARK_PALETTE], "dark"
        )
        self.assertIs(chosen, DARK_PALETTE)
        self.assertTrue(matched)

    def test_light_mode_skips_dark_palette(self):
        chosen, matched = _select_palette_for_mode(
            [DARK_PALETTE, LIGHT_PALETTE], "light"
        )
        self.assertIs(chosen, LIGHT_PALETTE)
        self.assertTrue(matched)

    def test_matching_top_hit_stays_first_for_each_mode(self):
        for palettes, mode, expected in (
            ([DARK_PALETTE, LIGHT_PALETTE], "dark", DARK_PALETTE),
            ([LIGHT_PALETTE, DARK_PALETTE], "light", LIGHT_PALETTE),
        ):
            with self.subTest(mode=mode):
                chosen, matched = _select_palette_for_mode(palettes, mode)
                self.assertIs(chosen, expected)
                self.assertTrue(matched)

    def test_malformed_palette_is_skipped_for_dark_mode(self):
        chosen, matched = _select_palette_for_mode(
            [MALFORMED_PALETTE, DARK_PALETTE], "dark"
        )
        self.assertIs(chosen, DARK_PALETTE)
        self.assertTrue(matched)

    def test_accessible_match_wins_within_requested_mode(self):
        chosen, matched = _select_palette_for_mode(
            [LOW_CONTRAST_DARK_PALETTE, DARK_PALETTE], "dark"
        )
        self.assertIs(chosen, DARK_PALETTE)
        self.assertTrue(matched)

    def test_missing_requested_mode_is_signaled(self):
        chosen, matched = _select_palette_for_mode([LIGHT_PALETTE], "dark")
        self.assertIs(chosen, LIGHT_PALETTE)
        self.assertFalse(matched)

        chosen, matched = _select_palette_for_mode([DARK_PALETTE], "light")
        self.assertIs(chosen, DARK_PALETTE)
        self.assertFalse(matched)

    def test_auto_mode_preserves_top_hit(self):
        chosen, matched = _select_palette_for_mode(
            [DARK_PALETTE, LIGHT_PALETTE], "auto"
        )
        self.assertIs(chosen, DARK_PALETTE)
        self.assertTrue(matched)

    def test_empty_results_are_signaled(self):
        self.assertEqual(_select_palette_for_mode([], "dark"), ({}, False))

    def test_mismatch_metadata_is_visible(self):
        metadata = _color_mode_metadata(
            {"requested": "dark", "source": "query"},
            LIGHT_PALETTE,
            False,
        )
        self.assertFalse(metadata["matched"])
        self.assertIn("No dark palette", metadata["warning"])

    def test_conflict_metadata_is_visible(self):
        metadata = _color_mode_metadata(
            {"requested": "conflict", "source": "query"},
            DARK_PALETTE,
            False,
        )
        self.assertFalse(metadata["matched"])
        self.assertIn("Conflicting light and dark", metadata["warning"])

    def test_low_contrast_metadata_is_visible(self):
        metadata = _color_mode_metadata(
            {"requested": "dark", "source": "query"},
            LOW_CONTRAST_DARK_PALETTE,
            True,
        )
        self.assertFalse(metadata["wcag_aa_normal_text"])
        self.assertIn("below WCAG AA", metadata["warning"])

    def test_malformed_palette_contrast_warning_is_visible(self):
        metadata = _color_mode_metadata(
            {"requested": "dark", "source": "query"},
            MALFORMED_PALETTE,
            False,
        )
        self.assertIsNone(metadata["contrast_ratio"])
        self.assertIn("contrast could not be calculated", metadata["warning"])


class TestAntiPatternPrecision(unittest.TestCase):
    def test_only_exact_contradictory_dark_clause_is_removed(self):
        result = _filter_anti_patterns_for_mode(
            "Excessive animation + Dark mode by default", "dark"
        )
        self.assertEqual(result, "Excessive animation")

    def test_terminal_punctuation_does_not_hide_exact_clause(self):
        self.assertEqual(
            _filter_anti_patterns_for_mode(
                "Dark mode by default. + Tiny tap targets", "dark"
            ),
            "Tiny tap targets",
        )

    def test_dark_accessibility_warning_is_preserved(self):
        original = "Low contrast in dark mode + Excessive animation"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "dark"), original)

    def test_dark_theme_safety_warning_is_preserved(self):
        original = "Dark theme needs visible focus"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "dark"), original)

    def test_unrelated_clause_is_preserved(self):
        original = "Complex jargon + Tiny tap targets"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "dark"), original)

    def test_forced_dark_clause_is_removed_without_losing_other_advice(self):
        self.assertEqual(
            _filter_anti_patterns_for_mode(
                "Forced dark mode + Tiny tap targets", "dark"
            ),
            "Tiny tap targets",
        )

    def test_light_clause_is_removed_only_for_light_mode(self):
        original = "Light mode default + Slow rendering"
        self.assertEqual(
            _filter_anti_patterns_for_mode(original, "light"), "Slow rendering"
        )
        self.assertEqual(_filter_anti_patterns_for_mode(original, "dark"), original)

    def test_dark_clause_is_a_no_op_for_light_mode(self):
        original = "Excessive animation + Dark mode by default"
        self.assertEqual(_filter_anti_patterns_for_mode(original, "light"), original)


class TestEndToEndCoherence(unittest.TestCase):
    def test_dark_primary_style_wires_through_generate(self):
        def fake_search(query, domain, max_results):
            del query, max_results
            if domain == "product":
                return {"results": [{"Product Type": "Fixture"}]}
            if domain == "style":
                return {
                    "results": [
                        {
                            "Style Category": "Dark Fixture",
                            "Light Mode ✓": "✗ No",
                            "Dark Mode ✓": "✓ Only",
                        }
                    ]
                }
            if domain == "color":
                return {"results": [LIGHT_PALETTE, DARK_PALETTE]}
            return {"results": []}

        generator = DesignSystemGenerator()
        generator._apply_reasoning = lambda category, results: {
            "pattern": "Fixture",
            "style_priority": [],
            "typography_mood": "",
            "key_effects": "",
            "anti_patterns": "Dark mode by default",
            "decision_rules": {},
            "severity": "MEDIUM",
        }
        with mock.patch.object(
            design_system_module, "search", side_effect=fake_search
        ):
            result = generator.generate("neutral fixture")
        self.assertEqual(result["color_mode"]["source"], "style")
        self.assertEqual(result["color_mode"]["requested"], "dark")
        self.assertEqual(_palette_mode(result["colors"]), "dark")
        self.assertEqual(result["anti_patterns"], "")

    def test_dark_query_has_coherent_palette_and_advice(self):
        result = DesignSystemGenerator().generate(
            "SaaS invoicing fintech B2B professional dark mode"
        )
        self.assertEqual(_palette_mode(result["colors"]), "dark")
        self.assertGreaterEqual(_contrast_ratio(result["colors"]), 4.5)
        self.assertNotIn("dark mode by default", result["anti_patterns"].lower())
        self.assertEqual(result["color_mode"]["requested"], "dark")
        self.assertTrue(result["color_mode"]["matched"])

    def test_negated_dark_query_stays_light(self):
        result = DesignSystemGenerator().generate("SaaS dashboard no dark mode")
        self.assertEqual(_palette_mode(result["colors"]), "light")
        self.assertEqual(result["color_mode"]["requested"], "light")

    def test_neutral_light_query_keeps_existing_top_hit(self):
        result = DesignSystemGenerator().generate("healthcare clinic booking app")
        self.assertEqual(_palette_mode(result["colors"]), "light")
        self.assertEqual(result["color_mode"]["requested"], "auto")

    def test_conflicting_query_surfaces_warning_in_json_and_formatted_notes(self):
        result = DesignSystemGenerator().generate(
            "support both dark mode and light mode"
        )
        self.assertFalse(result["color_mode"]["matched"])
        self.assertIn("Conflicting light and dark", result["color_mode"]["warning"])
        self.assertIn("WARNING: Conflicting light and dark", result["colors"]["notes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
