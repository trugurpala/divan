from __future__ import annotations

import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "plugins" / "sadrazam" / "divan_runtime"
PLUGIN_ROOT = RUNTIME.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


class TimeoutRuntimeIntegrationTests(unittest.TestCase):
    def test_timeout_modules_live_inside_existing_nine_module_contract(self) -> None:
        modules = json.loads(
            (RUNTIME / "modules.json").read_text(encoding="utf-8")
        )["modules"]
        self.assertEqual(len(modules), 9)
        by_id = {row["id"]: row for row in modules}
        self.assertIn("timeouts", by_id["kernel"]["python_modules"])
        self.assertIn("execution", by_id["evidence"]["python_modules"])
        self.assertIn("ci_guard", by_id["records"]["python_modules"])

    def test_packaged_timeout_data_is_byte_equal_to_registry_truth(self) -> None:
        from divan_runtime import contract_validation

        for name in ("timeout-policy.json", "timeout-benchmarks.json"):
            packaged = RUNTIME / "data" / name
            canonical = ROOT / "registry" / name
            self.assertIn(f"data/{name}", contract_validation.RUNTIME_DATA_FILES)
            self.assertEqual(packaged.read_bytes(), canonical.read_bytes())

    def test_default_decision_uses_packaged_offline_contract(self) -> None:
        from divan_runtime import timeouts

        decision = timeouts.resolve_default("verify")

        self.assertEqual(decision.source, "benchmark")
        self.assertEqual(decision.sample_count, 5)
        self.assertEqual(decision.configured_seconds, 300)

    def test_default_provider_runner_uses_adaptive_execution_once(self) -> None:
        from divan_runtime import execution, providers

        observed = execution.ExecutionResult(
            status="TIMEOUT",
            returncode=None,
            stdout="partial",
            stderr="",
            elapsed_seconds=300.0,
            timeout={"configured_seconds": 300},
            mutating=False,
            retry_allowed=True,
            next_action="Retry once with a reviewed controlled timeout.",
        )
        with mock.patch.object(
            providers.execution, "run", return_value=observed
        ) as run:
            completed = providers._default_runner(["gh", "auth", "status"])

        self.assertEqual(completed.returncode, 124)
        self.assertIn("divan-timeout", completed.stderr)
        run.assert_called_once()
        decision = run.call_args.args[1]
        self.assertEqual(decision.command_class, "provider")
        self.assertFalse(run.call_args.kwargs["mutating"])


if __name__ == "__main__":
    unittest.main()
