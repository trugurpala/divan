import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.pusula_checkpoint import (
    MAX_CAPSULE_CHARS,
    CapsuleError,
    compute_digest,
    render_markdown,
    seal_capsule,
    validate_capsule,
)

BASELINE_SHA = "68e91fdf48dbcc385be567f4b525a682eeb9af05"


def draft_capsule(**overrides):
    value = {
        "schema": 1,
        "project": "divan-pusula",
        "checkpoint_percent": 25,
        "baseline_sha": BASELINE_SHA,
        "constitution_version": "2.0.0",
        "plan_version": "2026-08-23.1",
        "active_spec": "specs/003-divan-pusula-web/spec.md",
        "completed_tasks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "decisions": [
            "Forgejo is canonical Git; GitHub is an optional mirror.",
            "Dagger owns canonical pipeline logic.",
        ],
        "verified_facts": [
            "Divan baseline is pinned to an exact Git SHA.",
            "Spec Kit constitution lives under .specify/memory.",
        ],
        "open_risks": ["Standalone divan-pusula repository has not been created yet."],
        "next_actions": ["Implement the next locked task and preserve exact evidence refs."],
        "evidence_refs": [
            "github:trugurpala/divan@68e91fdf48dbcc385be567f4b525a682eeb9af05",
            "specs/003-divan-pusula-web/spec.md",
        ],
        "budget": {"model_usd_used": 0.0, "model_usd_hard_limit": 2500.0},
    }
    value.update(overrides)
    return value


class CapsuleContractTests(unittest.TestCase):
    def test_seal_is_deterministic_and_valid(self):
        first = seal_capsule(draft_capsule())
        second = seal_capsule(draft_capsule())
        self.assertEqual(first, second)
        self.assertEqual(first["digest"], compute_digest(first))
        self.assertEqual(validate_capsule(first), first)

    def test_tampered_capsule_fails_digest_validation(self):
        sealed = seal_capsule(draft_capsule())
        sealed["next_actions"][0] = "Do something different."
        with self.assertRaisesRegex(CapsuleError, "digest mismatch"):
            validate_capsule(sealed)

    def test_checkpoint_must_be_quarter_boundary(self):
        with self.assertRaisesRegex(CapsuleError, "0, 25, 50, 75, 100"):
            seal_capsule(draft_capsule(checkpoint_percent=30))

    def test_baseline_must_be_exact_git_sha(self):
        with self.assertRaisesRegex(CapsuleError, "40-character Git SHA"):
            seal_capsule(draft_capsule(baseline_sha="main"))

    def test_pre_release_checkpoint_requires_next_action(self):
        with self.assertRaisesRegex(CapsuleError, "next_actions"):
            seal_capsule(draft_capsule(next_actions=[]))

    def test_100_percent_checkpoint_may_have_no_next_action(self):
        sealed = seal_capsule(draft_capsule(checkpoint_percent=100, next_actions=[]))
        self.assertEqual(sealed["checkpoint_percent"], 100)

    def test_completed_tasks_are_unique_and_in_locked_range(self):
        with self.assertRaisesRegex(CapsuleError, "duplicates"):
            seal_capsule(draft_capsule(completed_tasks=[1, 1]))
        with self.assertRaisesRegex(CapsuleError, "1 through 40"):
            seal_capsule(draft_capsule(completed_tasks=[41]))

    def test_absolute_or_parent_spec_path_is_rejected(self):
        with self.assertRaisesRegex(CapsuleError, "repository-relative"):
            seal_capsule(draft_capsule(active_spec="../secret/spec.md"))

    def test_raw_secret_fields_and_values_are_rejected(self):
        bad_field = draft_capsule(budget={"api_key": "not-even-a-real-key"})
        with self.assertRaisesRegex(CapsuleError, "raw secret field"):
            seal_capsule(bad_field)

        bad_value = draft_capsule(
            open_risks=["accidental credential sk-1234567890abcdef1234567890abcdef"]
        )
        with self.assertRaisesRegex(CapsuleError, "secret-like value"):
            seal_capsule(bad_value)

    def test_list_limits_bound_resume_context(self):
        too_many = [f"decision {index}" for index in range(13)]
        with self.assertRaisesRegex(CapsuleError, "item limit 12"):
            seal_capsule(draft_capsule(decisions=too_many))

    def test_character_budget_bounds_capsule(self):
        oversized = copy.deepcopy(draft_capsule())
        oversized["verified_facts"] = ["x" * 700 for _ in range(20)]
        with self.assertRaisesRegex(CapsuleError, "token-friendly character budget"):
            seal_capsule(oversized)

    def test_markdown_render_contains_only_resume_sections(self):
        sealed = seal_capsule(draft_capsule())
        rendered = render_markdown(sealed)
        self.assertIn("# Pusula checkpoint 25%", rendered)
        self.assertIn("## Accepted decisions", rendered)
        self.assertIn("## Next actions", rendered)
        self.assertIn(sealed["digest"], rendered)

    def test_cli_seal_validate_and_render_round_trip(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "scripts" / "pusula_checkpoint.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = root / "draft.json"
            sealed = root / "checkpoint-25.json"
            rendered = root / "checkpoint-25.md"
            draft.write_text(json.dumps(draft_capsule()), encoding="utf-8")

            seal_run = subprocess.run(
                [sys.executable, str(script), "seal", str(draft), str(sealed)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(seal_run.returncode, 0, seal_run.stderr)
            self.assertTrue(sealed.exists())

            validate_run = subprocess.run(
                [sys.executable, str(script), "validate", str(sealed)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate_run.returncode, 0, validate_run.stderr)
            self.assertEqual(json.loads(validate_run.stdout)["status"], "valid")

            render_run = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "render",
                    str(sealed),
                    "--output",
                    str(rendered),
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(render_run.returncode, 0, render_run.stderr)
            self.assertIn("Pusula checkpoint 25%", rendered.read_text(encoding="utf-8"))

    def test_unknown_fields_fail_closed(self):
        capsule = draft_capsule(extra_untracked_state="should not persist")
        with self.assertRaisesRegex(CapsuleError, "unknown fields"):
            seal_capsule(capsule)

    def test_capsule_constant_documents_token_budget(self):
        self.assertEqual(MAX_CAPSULE_CHARS, 12_000)


if __name__ == "__main__":
    unittest.main()
