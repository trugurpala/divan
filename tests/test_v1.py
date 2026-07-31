from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import adoption  # noqa: E402

from tests.test_adoption_v2 import clean_room_parts  # noqa: E402

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
        if passed == len(gates):
            self.assertIn("Bütün v1 hazırlık kapıları tamamlandı", text)
            self.assertNotIn("canlı kanıtı henüz kaydedilmedi", text)
        else:
            self.assertIn("Bütün kapılar geçmeden", text)
        if gates["real-agent-comparison"]["status"] == "passed":
            self.assertNotIn("Gerçek bir ajan adaptörü", text)
        else:
            self.assertIn("Gerçek bir ajan adaptörü", text)
        self.assertIn("makinece doğrulanabilir temiz-proje", text)

    def test_real_agent_and_clean_room_evidence_pass(self) -> None:
        gates = {gate["id"]: gate for gate in V1.oku(ROOT)["gates"]}
        self.assertEqual(gates["native-clean-host-matrix"]["status"], "passed")
        self.assertNotIn("independent-adoption", gates)
        self.assertEqual(
            gates["verified-clean-room-adoption"]["status"], "passed"
        )
        self.assertEqual(
            gates["verified-clean-room-adoption"]["release"]["ref"],
            "v0.18.5",
        )

    def write_clean_room_registry(
        self,
        root: pathlib.Path,
        *,
        receipt: dict[str, object] | None = None,
        status: str = "passed",
    ) -> pathlib.Path:
        evidence_path = (
            root
            / ".divan"
            / "evidence"
            / "verified-clean-room-adoption-v0183.json"
        )
        evidence_path.parent.mkdir(parents=True)
        value = (
            adoption.build_clean_room_receipt(**clean_room_parts())
            if receipt is None
            else receipt
        )
        evidence_path.write_bytes(adoption.serialize_adoption_json(value))
        divan = value["divan"]
        assert isinstance(divan, dict)
        registry = {
            "schema_version": 1,
            "target": "1.0.0",
            "updated": "2026-07-30",
            "gates": [
                {
                    "id": "verified-clean-room-adoption",
                    "title": "Doğrulanmış temiz-proje kullanımı",
                    "status": status,
                    "evidence": [
                        ".divan/evidence/"
                        "verified-clean-room-adoption-v0183.json"
                    ],
                    "release": {
                        key: divan[key]
                        for key in (
                            "version",
                            "ref",
                            "commit",
                            "runner_sha256",
                        )
                    },
                }
            ],
        }
        registry_path = root / "registry" / "v1-gates.json"
        registry_path.parent.mkdir()
        registry_path.write_text(
            json.dumps(registry, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return evidence_path

    def test_passed_clean_room_gate_loads_and_verifies_real_receipt(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="divan-v1-clean-room-"
        ) as temporary:
            root = pathlib.Path(temporary)
            self.write_clean_room_registry(root)

            gates = V1.oku(root)["gates"]

        self.assertEqual(gates[0]["status"], "passed")

    def test_passed_clean_room_gate_rejects_schema_1_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="divan-v1-clean-room-"
        ) as temporary:
            root = pathlib.Path(temporary)
            evidence_path = self.write_clean_room_registry(root)
            evidence_path.write_text(
                json.dumps(
                    {"schema_version": 1, "product": "divan-adoption"}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "schema 2|clean-room"):
                V1.oku(root)

        with tempfile.TemporaryDirectory(
            prefix="divan-v1-clean-room-"
        ) as temporary:
            root = pathlib.Path(temporary)
            evidence_path = self.write_clean_room_registry(root)
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            payload["checks"][0]["exit_code"] = 7
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid|clean-room"):
                V1.oku(root)

    def test_passed_clean_room_gate_rejects_release_mismatch(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="divan-v1-clean-room-"
        ) as temporary:
            root = pathlib.Path(temporary)
            self.write_clean_room_registry(root)
            registry_path = root / "registry" / "v1-gates.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["gates"][0]["release"]["commit"] = "b" * 40
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "release identity"):
                V1.oku(root)

    def test_real_agent_evidence_schema_rejects_public_mapping_leaks(self) -> None:
        path = ROOT / "evals" / "results" / "claude-codex-baglam-muhafizi-v012.json"
        evidence = json.loads(path.read_text(encoding="utf-8"))
        V1._validate_real_agent_evidence(evidence, path)

        leaked = copy.deepcopy(evidence)
        leaked["cases"][0]["judgement"]["winner"] = "A"
        with self.assertRaisesRegex(ValueError, "private key"):
            V1._validate_real_agent_evidence(leaked, path)

        missing_model = copy.deepcopy(evidence)
        del missing_model["provenance"]["agent_model"]
        with self.assertRaisesRegex(ValueError, "agent_model"):
            V1._validate_real_agent_evidence(missing_model, path)

        leaked_seed = copy.deepcopy(evidence)
        leaked_seed["provenance"]["blind_seed"] = "17"
        with self.assertRaisesRegex(ValueError, "private key"):
            V1._validate_real_agent_evidence(leaked_seed, path)


if __name__ == "__main__":
    unittest.main()
