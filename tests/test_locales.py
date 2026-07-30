from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "plugins" / "sadrazam" / "divan_runtime"
MODULE_PATH = RUNTIME / "locales.py"


def load_locales():
    if not MODULE_PATH.is_file():
        raise AssertionError("locales.py is missing")
    spec = importlib.util.spec_from_file_location("divan_locales_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocaleTests(unittest.TestCase):
    def test_catalog_has_exact_en_tr_parity_and_matching_placeholders(self) -> None:
        module = load_locales()
        catalog = module.load_messages(RUNTIME)

        self.assertIn("progress.current_task", catalog)
        for key in (
            "navigation.skip",
            "navigation.progress",
            "progress.summary",
            "progress.live_summary",
            "technical.tasks",
            "connection.missing_capability",
            "state.current",
            "task.test_first_implementation",
            "task.independent_review",
        ):
            self.assertIn(key, catalog)
        for key, translations in catalog.items():
            with self.subTest(key=key):
                self.assertEqual(set(translations), {"en", "tr"})
                self.assertEqual(
                    module.placeholders(translations["en"]),
                    module.placeholders(translations["tr"]),
                )

    def test_language_resolution_is_bounded(self) -> None:
        module = load_locales()

        self.assertEqual(module.resolve_language("tr"), "tr")
        self.assertEqual(module.resolve_language("en"), "en")
        self.assertEqual(
            module.resolve_language("auto", {"LANG": "tr_TR.UTF-8"}),
            "tr",
        )
        self.assertEqual(
            module.resolve_language("auto", {"LANG": "de_DE.UTF-8"}),
            "en",
        )
        self.assertEqual(module.resolve_language(None, {}), "en")
        self.assertEqual(
            module.resolve_language(
                "auto",
                {"LANG": "C.UTF-8"},
                system_locale="tr_TR",
            ),
            "tr",
        )
        with self.assertRaisesRegex(ValueError, "language must be auto, en, or tr"):
            module.resolve_language("de")

    def test_message_formats_only_declared_placeholders(self) -> None:
        module = load_locales()
        catalog = module.load_messages(RUNTIME)

        self.assertEqual(
            module.message(
                catalog,
                "progress.task_count",
                "tr",
                complete=3,
                total=5,
            ),
            "3 / 5 görev tamamlandı",
        )
        with self.assertRaisesRegex(ValueError, "unknown message key"):
            module.message(catalog, "missing.key", "en")
        with self.assertRaisesRegex(ValueError, "message values do not match"):
            module.message(catalog, "progress.task_count", "en", complete=3)


if __name__ == "__main__":
    unittest.main()
