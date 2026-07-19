from __future__ import annotations

import csv
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_legacy_state", ROOT / "scripts" / "legacy_state.py"
)
assert SPEC and SPEC.loader
LEGACY_STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LEGACY_STATE)


class LegacyStateTests(unittest.TestCase):
    def _skill(self, path: pathlib.Path, content: str) -> None:
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(content, encoding="utf-8")

    def _manifest(
        self,
        path: pathlib.Path,
        rows: list[dict[str, str]],
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                delimiter="\t",
                fieldnames=(
                    "skill",
                    "hedef",
                    "yedek",
                    "installed_sha256",
                ),
            )
            writer.writeheader()
            writer.writerows(rows)

    def test_changed_target_is_rejected_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            skills = base / "skills"
            state = base / "state"
            target = skills / "sadrazam"
            backup = state / "divan-backups" / "old" / "sadrazam"
            self._skill(target, "installed")
            self._skill(backup, "user copy")
            expected = LEGACY_STATE.tree_digest(target)
            manifest = state / "install.tsv"
            state.mkdir(exist_ok=True)
            self._manifest(
                manifest,
                [
                    {
                        "skill": "sadrazam",
                        "hedef": str(target),
                        "yedek": str(backup),
                        "installed_sha256": expected,
                    }
                ],
            )
            (target / "SKILL.md").write_text("later replacement", encoding="utf-8")

            with self.assertRaisesRegex(LEGACY_STATE.LegacyStateError, "changed"):
                LEGACY_STATE.migrate_legacy(manifest, skills, state)

            self.assertEqual((target / "SKILL.md").read_text(), "later replacement")
            self.assertEqual((backup / "SKILL.md").read_text(), "user copy")

    def test_failure_after_rows_restores_every_target_and_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            skills = base / "skills"
            state = base / "state"
            rows: list[dict[str, str]] = []
            for name in ("sadrazam", "defterdar"):
                target = skills / name
                backup = state / "divan-backups" / "old" / name
                self._skill(target, f"installed {name}")
                self._skill(backup, f"user {name}")
                rows.append(
                    {
                        "skill": name,
                        "hedef": str(target),
                        "yedek": str(backup),
                        "installed_sha256": LEGACY_STATE.tree_digest(target),
                    }
                )
            manifest = state / "install.tsv"
            state.mkdir(exist_ok=True)
            self._manifest(manifest, rows)

            with self.assertRaisesRegex(LEGACY_STATE.LegacyStateError, "fixture failure"):
                LEGACY_STATE.migrate_legacy(manifest, skills, state, fail_after=1)

            for name in ("sadrazam", "defterdar"):
                self.assertEqual(
                    (skills / name / "SKILL.md").read_text(), f"installed {name}"
                )
                self.assertEqual(
                    (state / "divan-backups" / "old" / name / "SKILL.md").read_text(),
                    f"user {name}",
                )


if __name__ == "__main__":
    unittest.main()
