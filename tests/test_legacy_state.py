from __future__ import annotations

import csv
import importlib.util
import json
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

    def test_durable_migration_journal_recovers_after_process_loss(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            skills = base / "skills"
            state = base / "state"
            target = skills / "sadrazam"
            backup = state / "divan-backups" / "old" / "sadrazam"
            quarantine = state / "divan-quarantine" / "crash" / "sadrazam"
            self._skill(quarantine, "installed")
            self._skill(target, "user copy")
            journal = state / "divan-transactions" / "crash.json"
            journal.parent.mkdir(parents=True)
            journal.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "kind": "migration",
                        "status": "in-progress",
                        "skills_dir": str(skills),
                        "state_dir": str(state),
                        "pending": {"kind": "restore-backup", "name": "sadrazam"},
                        "operations": [
                            {
                                "name": "sadrazam",
                                "target": str(target),
                                "backup": str(backup),
                                "owned": str(quarantine),
                                "quarantined": True,
                                "backup_restored": True,
                                "recovered": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            recovered = LEGACY_STATE.recover_legacy(journal)

            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual((target / "SKILL.md").read_text(), "installed")
            self.assertEqual((backup / "SKILL.md").read_text(), "user copy")

    def test_recovery_leaves_an_unprocessed_row_with_a_missing_backup_untouched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            skills = base / "skills"
            state = base / "state"
            target = skills / "sadrazam"
            backup = state / "divan-backups" / "old" / "sadrazam"
            owned = state / "divan-quarantine" / "crash" / "sadrazam"
            self._skill(target, "installed")
            journal = state / "divan-transactions" / "crash.json"
            journal.parent.mkdir(parents=True)
            journal.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "kind": "migration",
                        "status": "in-progress",
                        "skills_dir": str(skills),
                        "state_dir": str(state),
                        "pending": None,
                        "operations": [
                            {
                                "name": "sadrazam",
                                "target": str(target),
                                "backup": str(backup),
                                "owned": str(owned),
                                "quarantined": False,
                                "backup_restored": False,
                                "recovered": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            recovered = LEGACY_STATE.recover_legacy(journal)

            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual((target / "SKILL.md").read_text(), "installed")
            self.assertFalse(backup.exists())
            self.assertFalse(owned.exists())

    def test_completed_migration_can_be_reversed_by_the_parent_transaction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            skills = base / "skills"
            state = base / "state"
            target = skills / "sadrazam"
            owned = state / "divan-quarantine" / "completed" / "sadrazam"
            self._skill(owned, "installed")
            journal = state / "divan-transactions" / "completed.json"
            journal.parent.mkdir(parents=True)
            journal.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "kind": "migration",
                        "status": "quarantined",
                        "skills_dir": str(skills),
                        "state_dir": str(state),
                        "pending": None,
                        "operations": [
                            {
                                "name": "sadrazam",
                                "target": str(target),
                                "backup": "",
                                "owned": str(owned),
                                "quarantined": True,
                                "backup_restored": False,
                                "recovered": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            recovered = LEGACY_STATE.recover_legacy(journal)

            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual((target / "SKILL.md").read_text(), "installed")
            self.assertFalse(owned.exists())

    def test_fallback_install_failure_reverses_all_completed_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-legacy-") as temporary:
            base = pathlib.Path(temporary)
            source = base / "source"
            skills = base / "skills"
            state = base / "state"
            for name in ("sadrazam", "defterdar"):
                self._skill(source / "plugins" / "pack" / "skills" / name, f"new {name}")
                self._skill(skills / name, f"user {name}")

            with self.assertRaisesRegex(LEGACY_STATE.LegacyStateError, "rolled back"):
                LEGACY_STATE.install_legacy(
                    source,
                    skills,
                    state,
                    {
                        "version": "0.12.0",
                        "ref": "v0.12.0",
                        "source_commit": "a" * 40,
                        "archive_sha256": "b" * 64,
                        "installed_at": "2026-07-19T00:00:00Z",
                    },
                    fail_after=1,
                )

            for name in ("sadrazam", "defterdar"):
                self.assertEqual((skills / name / "SKILL.md").read_text(), f"user {name}")


if __name__ == "__main__":
    unittest.main()
