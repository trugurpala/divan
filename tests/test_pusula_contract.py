from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts import pusula_checkpoint_core as checkpoint_core
from scripts import pusula_contract as contract

BASELINE_SHA = "68e91fdf48dbcc385be567f4b525a682eeb9af05"


def _plan() -> dict[str, object]:
    tasks = [[index, f"Task {index}"] for index in range(1, 41)]
    layers = []
    for index, layer_id in enumerate("ABCDEFGHIJ"):
        start = index * 4 + 1
        layers.append(
            {
                "id": layer_id,
                "name": f"Layer {layer_id}",
                "tasks": list(range(start, start + 4)),
            }
        )
    return {
        "schema": 1,
        "plan_version": "2026-08-23.1",
        "constitution_version": "2.0.0",
        "baseline": {
            "repository": "trugurpala/divan",
            "sha": BASELINE_SHA,
            "source_version": "1.3.8",
            "canonical_test_count": 1020,
            "canonical_skips": 11,
            "coverage_percent": 75,
        },
        "target_product": "Divan Pusula 1.0.0",
        "target_repository": "trugurpala/divan-pusula",
        "incubation_branch": "feat/pusula-bootstrap-20260823",
        "change_rule": "Only evidence-backed contradictions may amend the locked plan.",
        "checkpoints": [0, 25, 50, 75, 100],
        "layers": layers,
        "tasks": tasks,
        "provider_posture": {"canonical_git": "Forgejo"},
        "upstream_pins": {"ecc": {"repo": "affaan-m/ECC"}},
    }


def _capsule(percent: int = 0, completed: list[int] | None = None) -> dict[str, object]:
    return checkpoint_core.seal_capsule(
        {
            "schema": 1,
            "project": "Divan Pusula",
            "checkpoint_percent": percent,
            "baseline_sha": BASELINE_SHA,
            "constitution_version": "2.0.0",
            "plan_version": "2026-08-23.1",
            "active_spec": "specs/003-divan-pusula-web/spec.md",
            "completed_tasks": completed or [],
            "decisions": ["Keep provider services replaceable."],
            "verified_facts": ["The fixture is intentionally bounded."],
            "open_risks": ["Fixture risk."],
            "next_actions": [] if percent == 100 else ["Continue."],
            "evidence_refs": ["fixture:evidence"],
            "budget": {"capsule_max_chars": 12000},
        }
    )


class PusulaContractTests(unittest.TestCase):
    def _root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / ".pusula" / "continuity").mkdir(parents=True)
        (root / "specs" / "003-divan-pusula-web").mkdir(parents=True)
        (root / "specs" / "003-divan-pusula-web" / "spec.md").write_text(
            "# fixture\n", encoding="utf-8"
        )
        (root / ".pusula" / "plan-lock.json").write_text(
            json.dumps(_plan()), encoding="utf-8"
        )
        return temporary, root

    @staticmethod
    def _write_checkpoint(root: Path, capsule: dict[str, object], name: str) -> None:
        (root / ".pusula" / "continuity" / name).write_text(
            json.dumps(capsule), encoding="utf-8"
        )

    def test_valid_plan_and_checkpoint_chain(self) -> None:
        temporary, root = self._root()
        with temporary:
            self._write_checkpoint(root, _capsule(0, [1, 2, 3, 4]), "checkpoint-00.json")
            result = contract.check(root)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["latest_checkpoint_percent"], 0)
        self.assertEqual(result["completed_task_count"], 4)

    def test_plan_schema_is_exact(self) -> None:
        value = _plan()
        value["unexpected"] = True
        with self.assertRaisesRegex(contract.ContractError, "plan-lock schema"):
            contract.validate_plan(value)

    def test_baseline_requires_exact_git_sha(self) -> None:
        value = _plan()
        baseline = value["baseline"]
        self.assertIsInstance(baseline, dict)
        baseline["sha"] = "main"
        with self.assertRaisesRegex(contract.ContractError, "exact lowercase Git SHA"):
            contract.validate_plan(value)

    def test_locked_plan_requires_exactly_forty_tasks(self) -> None:
        value = _plan()
        tasks = value["tasks"]
        self.assertIsInstance(tasks, list)
        tasks.pop()
        with self.assertRaisesRegex(contract.ContractError, "exactly 40"):
            contract.validate_plan(value)

    def test_layers_must_cover_each_task_once(self) -> None:
        value = _plan()
        layers = value["layers"]
        self.assertIsInstance(layers, list)
        self.assertIsInstance(layers[1], dict)
        layers[1]["tasks"] = [1, 6, 7, 8]
        with self.assertRaisesRegex(contract.ContractError, "cover every task exactly once"):
            contract.validate_plan(value)

    def test_checkpoint_is_required(self) -> None:
        temporary, root = self._root()
        with temporary:
            with self.assertRaisesRegex(contract.ContractError, "at least one"):
                contract.check(root)

    def test_checkpoint_filename_must_match_payload(self) -> None:
        temporary, root = self._root()
        with temporary:
            self._write_checkpoint(root, _capsule(25, list(range(1, 11))), "checkpoint-00.json")
            with self.assertRaisesRegex(contract.ContractError, "filename and payload disagree"):
                contract.check(root)

    def test_tampered_digest_fails_closed(self) -> None:
        temporary, root = self._root()
        capsule = _capsule(0)
        capsule["project"] = "tampered"
        with temporary:
            self._write_checkpoint(root, capsule, "checkpoint-00.json")
            with self.assertRaisesRegex(contract.ContractError, "digest mismatch"):
                contract.check(root)

    def test_checkpoint_versions_must_match_locked_plan(self) -> None:
        temporary, root = self._root()
        capsule = _capsule(0)
        capsule["plan_version"] = "future"
        resealed = checkpoint_core.seal_capsule(capsule)
        with temporary:
            self._write_checkpoint(root, resealed, "checkpoint-00.json")
            with self.assertRaisesRegex(contract.ContractError, "plan version drift"):
                contract.check(root)

    def test_completed_tasks_are_monotonic_across_checkpoints(self) -> None:
        temporary, root = self._root()
        first = _capsule(0, [1, 2, 3, 4])
        second = _capsule(25, [1, 2, 3])
        with temporary:
            self._write_checkpoint(root, first, "checkpoint-00.json")
            self._write_checkpoint(root, second, "checkpoint-25.json")
            with self.assertRaisesRegex(contract.ContractError, "monotonic"):
                contract.check(root)

    def test_active_spec_must_exist(self) -> None:
        temporary, root = self._root()
        with temporary:
            (root / "specs" / "003-divan-pusula-web" / "spec.md").unlink()
            self._write_checkpoint(root, _capsule(0), "checkpoint-00.json")
            with self.assertRaisesRegex(contract.ContractError, "active spec does not exist"):
                contract.check(root)

    def test_validate_plan_does_not_mutate_input(self) -> None:
        value = _plan()
        before = deepcopy(value)
        contract.validate_plan(value)
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
