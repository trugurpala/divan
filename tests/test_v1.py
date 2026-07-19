from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_v1", ROOT / "scripts" / "v1.py")
assert SPEC and SPEC.loader
V1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V1)


class V1GateTests(unittest.TestCase):
    def test_generated_scorecard_is_current(self) -> None:
        V1.denetle(ROOT)
        gates = {gate["id"]: gate for gate in V1.oku(ROOT)["gates"]}
        passed = sum(gate["status"] == "passed" for gate in gates.values())
        text = (ROOT / "docs/V1-Hazirlik.md").read_text(encoding="utf-8")
        self.assertIn(f"{passed}/{len(gates)} kapı", text)
        self.assertIn("0 kapının otomasyonu hazır", text)
        self.assertIn("Bütün kapılar geçmeden", text)
        if gates["real-agent-comparison"]["status"] == "passed":
            self.assertNotIn("Gerçek bir ajan adaptörü", text)
        else:
            self.assertIn("Gerçek bir ajan adaptörü", text)
        self.assertIn("Proje sahibi dışındaki", text)

    def test_real_agent_evidence_passes_and_adoption_remains_pending(self) -> None:
        gates = {gate["id"]: gate for gate in V1.oku(ROOT)["gates"]}
        self.assertEqual(gates["native-clean-host-matrix"]["status"], "passed")
        self.assertEqual(gates["independent-adoption"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
