from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_release_guard", ROOT / "scripts" / "release_guard.py"
)
assert SPEC and SPEC.loader
RELEASE_GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE_GUARD)


class ReleaseGuardTests(unittest.TestCase):
    @staticmethod
    def _assets(tag: str = "v1.2.3") -> list[dict[str, str]]:
        names = RELEASE_GUARD.FIXED_ASSETS | {
            f"divan-{tag}.zip",
            f"divan-{tag}.sha256",
            f"divan-{tag}.spdx.json",
        }
        return [{"name": name} for name in sorted(names)]

    @staticmethod
    def _bundle(
        root: pathlib.Path,
        *,
        tag: str = "v1.2.3",
        source_commit: str = "a" * 40,
    ) -> None:
        names = (
            f"divan-{tag}.zip",
            f"divan-{tag}.spdx.json",
            "divan-project.pyz",
            "divan-project.pyz.sha256",
            "divan.pyz",
            "divan.pyz.sha256",
        )
        lines: list[str] = []
        for name in names:
            payload = f"fixture:{name}\n".encode()
            (root / name).write_bytes(payload)
            lines.append(f"{hashlib.sha256(payload).hexdigest()}  {name}")
        lines.extend((f"source_commit={source_commit}", f"tag={tag}"))
        (root / f"divan-{tag}.sha256").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        (root / "divan-release-notes.md").write_text(
            "# Fixture release\n",
            encoding="utf-8",
        )

    def test_requires_enabled_immutable_releases(self) -> None:
        RELEASE_GUARD.require_immutable_releases(
            {"enabled": True, "enforced_by_owner": False}
        )
        unsafe_values: tuple[object, ...] = ({"enabled": False}, {}, [])
        for value in unsafe_values:
            with self.subTest(value=value), self.assertRaisesRegex(
                RELEASE_GUARD.ReleaseGuardError, "not enabled"
            ):
                RELEASE_GUARD.require_immutable_releases(value)

    def test_requires_active_no_bypass_stable_tag_ruleset(self) -> None:
        ruleset = {
            "target": "tag",
            "enforcement": "active",
            "bypass_actors": [],
            "conditions": {
                "ref_name": {
                    "include": ["refs/tags/v*"],
                    "exclude": [],
                }
            },
            "rules": [{"type": "update"}, {"type": "deletion"}],
        }
        RELEASE_GUARD.require_tag_ruleset(ruleset, "v1.2.3")

        unsafe = {
            "disabled": {**ruleset, "enforcement": "disabled"},
            "bypass": {**ruleset, "bypass_actors": [{"actor_type": "User"}]},
            "missing-bypass-proof": {
                key: value for key, value in ruleset.items() if key != "bypass_actors"
            },
            "wrong-target": {**ruleset, "target": "branch"},
            "excluded": {
                **ruleset,
                "conditions": {
                    "ref_name": {
                        "include": ["refs/tags/v*"],
                        "exclude": ["refs/tags/v1.2.3"],
                    }
                },
            },
            "movable": {**ruleset, "rules": [{"type": "deletion"}]},
        }
        for name, value in unsafe.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                RELEASE_GUARD.ReleaseGuardError, "does not lock"
            ):
                RELEASE_GUARD.require_tag_ruleset(value, "v1.2.3")

    def test_release_list_distinguishes_missing_and_immutable_published(self) -> None:
        self.assertEqual(
            RELEASE_GUARD.release_state([[], [{"tag_name": "v1.2.2"}]], "v1.2.3"),
            "missing",
        )
        release = {
            "tag_name": "v1.2.3",
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "published_at": "2026-08-04T00:00:00Z",
            "assets": self._assets(),
        }
        self.assertEqual(
            RELEASE_GUARD.release_state([[release]], "v1.2.3"),
            "published",
        )

    def test_release_list_rejects_draft_mutable_and_duplicate_records(self) -> None:
        valid = {
            "tag_name": "v1.2.3",
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "published_at": "2026-08-04T00:00:00Z",
            "assets": self._assets(),
        }
        cases = {
            "draft": [{**valid, "draft": True}],
            "mutable": [{**valid, "immutable": False}],
            "unpublished": [{**valid, "published_at": None}],
            "duplicate": [valid, dict(valid)],
        }
        for name, rows in cases.items():
            with self.subTest(name=name), self.assertRaises(
                RELEASE_GUARD.ReleaseGuardError
            ):
                RELEASE_GUARD.release_state([rows], "v1.2.3")

    def test_release_list_rejects_missing_extra_and_duplicate_assets(self) -> None:
        valid = {
            "tag_name": "v1.2.3",
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "published_at": "2026-08-04T00:00:00Z",
        }
        assets = self._assets()
        cases = {
            "missing": assets[:-1],
            "extra": [*assets, {"name": "unreviewed.bin"}],
            "duplicate": [*assets, dict(assets[0])],
            "invalid": [{"name": None}],
        }
        for name, rows in cases.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                RELEASE_GUARD.ReleaseGuardError, "exact release contract"
            ):
                RELEASE_GUARD.release_state(
                    [[{**valid, "assets": rows}]],
                    "v1.2.3",
                )

    def test_release_bundle_binds_exact_files_hashes_tag_and_commit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-bundle-") as temporary:
            root = pathlib.Path(temporary)
            self._bundle(root)
            self.assertEqual(
                RELEASE_GUARD.require_release_bundle(root, "v1.2.3"),
                "a" * 40,
            )

    def test_release_bundle_rejects_tampering_and_unexpected_entries(self) -> None:
        cases = ("asset", "checksum-path", "metadata", "extra")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory(
                prefix="divan-release-bundle-"
            ) as temporary:
                root = pathlib.Path(temporary)
                self._bundle(root)
                checksum = root / "divan-v1.2.3.sha256"
                if case == "asset":
                    (root / "divan.pyz").write_bytes(b"tampered\n")
                elif case == "checksum-path":
                    text = checksum.read_text(encoding="utf-8")
                    checksum.write_text(
                        text.replace("  divan-v1.2.3.zip", "  ../VERSION", 1),
                        encoding="utf-8",
                    )
                elif case == "metadata":
                    text = checksum.read_text(encoding="utf-8")
                    checksum.write_text(
                        text.replace("source_commit=" + "a" * 40, "source_commit=main"),
                        encoding="utf-8",
                    )
                else:
                    (root / "unexpected.bin").write_bytes(b"unexpected\n")

                with self.assertRaises(RELEASE_GUARD.ReleaseGuardError):
                    RELEASE_GUARD.require_release_bundle(root, "v1.2.3")

    def test_rejects_non_stable_tag(self) -> None:
        with self.assertRaisesRegex(
            RELEASE_GUARD.ReleaseGuardError, "stable SemVer"
        ):
            RELEASE_GUARD.release_state([[]], "latest")


if __name__ == "__main__":
    unittest.main()
