from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


class TimeoutPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        from divan_runtime import timeouts

        self.timeouts = timeouts
        self.policy = self.timeouts.load_json(
            ROOT / "registry" / "timeout-policy.json"
        )
        self.benchmarks = self.timeouts.load_json(
            ROOT / "registry" / "timeout-benchmarks.json"
        )

    def test_registry_contract_has_exact_command_classes(self) -> None:
        self.timeouts.validate_policy(self.policy)
        self.assertEqual(
            set(self.policy["classes"]),
            {
                "browser",
                "fast-check",
                "provider",
                "release",
                "security",
                "test",
                "verify",
            },
        )

    def test_trusted_samples_use_nearest_rank_p95_margin_and_caps(self) -> None:
        policy = {
            "schema_version": 1,
            "minimum_trusted_samples": 5,
            "percentile": 95,
            "safety_margin": {"numerator": 3, "denominator": 2},
            "trusted": {
                "repository": "owner/repo",
                "branch": "main",
                "events": ["push"],
            },
            "classes": {
                "verify": {
                    "default_seconds": 200,
                    "minimum_seconds": 100,
                    "maximum_seconds": 300,
                    "workflows": ["quality.yml"],
                }
            },
        }
        runs = [
            {
                "workflow": "quality.yml",
                "run_id": index,
                "event": "push",
                "conclusion": "success",
                "branch": "main",
                "duration_seconds": seconds,
            }
            for index, seconds in enumerate((10, 20, 30, 40, 250), start=1)
        ]
        benchmarks = {
            "schema_version": 1,
            "source_repository": "owner/repo",
            "collected_at": "2026-07-30T00:00:00Z",
            "runs": runs,
        }

        decision = self.timeouts.resolve("verify", policy, benchmarks)

        self.assertEqual(decision.source, "benchmark")
        self.assertEqual(decision.sample_count, 5)
        self.assertEqual(decision.percentile_seconds, 250)
        self.assertEqual(decision.configured_seconds, 300)

    def test_untrusted_and_unsuccessful_rows_do_not_train_policy(self) -> None:
        benchmarks = json.loads(json.dumps(self.benchmarks))
        benchmarks["runs"].extend(
            [
                {
                    "workflow": "quality-gate.yml",
                    "run_id": 999001,
                    "event": "pull_request",
                    "conclusion": "success",
                    "branch": "main",
                    "duration_seconds": 9999,
                },
                {
                    "workflow": "quality-gate.yml",
                    "run_id": 999002,
                    "event": "push",
                    "conclusion": "failure",
                    "branch": "main",
                    "duration_seconds": 9999,
                },
                {
                    "workflow": "quality-gate.yml",
                    "run_id": 999003,
                    "event": "push",
                    "conclusion": "success",
                    "branch": "feature/untrusted",
                    "duration_seconds": 9999,
                },
            ]
        )

        original = self.timeouts.resolve(
            "verify", self.policy, self.benchmarks
        )
        observed = self.timeouts.resolve("verify", self.policy, benchmarks)

        self.assertEqual(observed, original)

    def test_insufficient_samples_and_corrupt_evidence_use_finite_default(self) -> None:
        sparse = {
            "schema_version": 1,
            "source_repository": "trugurpala/divan",
            "collected_at": "2026-07-30T00:00:00Z",
            "runs": [],
        }
        decision = self.timeouts.resolve("test", self.policy, sparse)
        corrupt = self.timeouts.resolve("verify", self.policy, {"runs": "bad"})
        unknown = self.timeouts.resolve("not-declared", {"bad": True}, {})

        self.assertEqual(decision.source, "default-insufficient-samples")
        self.assertEqual(decision.configured_seconds, 600)
        self.assertEqual(corrupt.source, "default-invalid-benchmark")
        self.assertEqual(corrupt.configured_seconds, 600)
        self.assertEqual(unknown.source, "safe-fallback")
        self.assertEqual(unknown.configured_seconds, 300)

    def test_override_is_explicit_and_must_remain_inside_class_bounds(self) -> None:
        decision = self.timeouts.resolve(
            "verify",
            self.policy,
            self.benchmarks,
            override_seconds=450,
        )
        self.assertEqual(decision.source, "override")
        self.assertEqual(decision.configured_seconds, 450)
        with self.assertRaisesRegex(ValueError, "safety bounds"):
            self.timeouts.resolve(
                "verify",
                self.policy,
                self.benchmarks,
                override_seconds=1,
            )
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.timeouts.resolve(
                "verify",
                self.policy,
                self.benchmarks,
                override_seconds=True,
            )


if __name__ == "__main__":
    unittest.main()
