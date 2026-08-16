from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.spec_compiler import compile_specification
from divan_runtime.spec_contract import QUALITY_PROFILES


def specification(**overrides):
    payload = {
        "ferman": "Ekip için iş takip uygulaması kur.",
        "outcome": "Bir ekip işleri atayabilsin, durumunu görebilsin ve raporlayabilsin.",
        "quality_profile": "WEB_STANDARD",
        "stories": [
            {
                "id": "assign",
                "title": "İş atama",
                "priority": "P1",
                "narrative": "Yönetici bir işi bir kişiye atar.",
                "acceptance": ["Atanan kişi işi kendi listesinde görür."],
            },
            {
                "id": "report",
                "title": "Raporlama",
                "priority": "P2",
                "narrative": "Yönetici haftalık durum raporu alır.",
                "acceptance": ["Rapor tamamlanan ve bekleyen işleri ayırır."],
            },
        ],
        "requirements": ["Sunucu tarafında yetki denetimi zorunludur."],
        "measurable_outcomes": ["Bir iş 3 tıklamada atanabilir."],
        "entities": ["Task", "User"],
        "edge_cases": ["Atanan kişi silinirse iş sahipsiz kalmamalı."],
        "assumptions": ["Tek kuruluş, tek zaman dilimi."],
    }
    payload.update(overrides)
    return payload


class SpecCompilerTests(unittest.TestCase):
    def assertRejects(self, code: str, payload) -> None:
        result = compile_specification(payload)
        self.assertFalse(result.ok, f"{code} was accepted")
        self.assertIsNone(result.specification)
        self.assertIn(
            code,
            {issue.code for issue in result.issues},
            f"expected {code}, got {[i.code for i in result.issues]}",
        )

    def test_a_complete_specification_compiles(self) -> None:
        result = compile_specification(specification())
        self.assertTrue(result.ok, [i.code for i in result.issues])
        assert result.specification is not None
        self.assertEqual(result.specification.project.outcome.startswith("Bir ekip"), True)
        self.assertEqual(len(result.specification.project.stories), 2)

    def test_compiling_never_grants_execution_authority(self) -> None:
        payload = compile_specification(specification()).to_dict()
        self.assertEqual(
            payload["specification"]["execution_authority"], "not-granted"
        )

    def test_work_packages_follow_priority_and_stay_parallel_within_a_band(self) -> None:
        result = compile_specification(
            specification(
                stories=[
                    {
                        "id": "a",
                        "title": "A",
                        "priority": "P1",
                        "narrative": "n",
                        "acceptance": ["x"],
                    },
                    {
                        "id": "b",
                        "title": "B",
                        "priority": "P1",
                        "narrative": "n",
                        "acceptance": ["x"],
                    },
                    {
                        "id": "c",
                        "title": "C",
                        "priority": "P2",
                        "narrative": "n",
                        "acceptance": ["x"],
                    },
                ]
            )
        )
        self.assertTrue(result.ok, [i.code for i in result.issues])
        assert result.specification is not None
        dag = result.specification.work_packages
        by_id = {node.package_id: node for node in dag.nodes}

        # Same priority band: independent, so both are ready immediately.
        self.assertEqual(by_id["WP-P1-a"].depends_on, ())
        self.assertEqual(by_id["WP-P1-b"].depends_on, ())
        self.assertEqual(set(dag.ready), {"WP-P1-a", "WP-P1-b"})
        # Lower band waits for the whole band above it.
        self.assertEqual(set(by_id["WP-P2-c"].depends_on), {"WP-P1-a", "WP-P1-b"})

    def test_quality_profile_selects_real_gates(self) -> None:
        for profile in QUALITY_PROFILES:
            result = compile_specification(specification(quality_profile=profile))
            self.assertTrue(result.ok, [i.code for i in result.issues])
            assert result.specification is not None
            quality = result.specification.quality
            self.assertEqual(quality.profile, profile)
            # A profile may add obligations, never remove a baseline gate.
            for gate in ("tests", "typecheck", "lint", "independent-review"):
                self.assertIn(gate, quality.required_gates)

        payment = compile_specification(specification(quality_profile="WEB_PAYMENT"))
        internal = compile_specification(specification(quality_profile="INTERNAL_TOOL"))
        assert payment.specification is not None and internal.specification is not None
        self.assertIn("authz-negative", payment.specification.quality.required_gates)
        self.assertIn("secret-scan", payment.specification.quality.required_gates)
        self.assertNotIn("authz-negative", internal.specification.quality.required_gates)

    def test_an_unresolved_clarification_marker_blocks_compilation(self) -> None:
        # The whole point of compiling is to stop a plan inventing product intent.
        self.assertRejects(
            "SPEC_CLARIFICATION_UNRESOLVED",
            specification(outcome="Raporlama [NEEDS CLARIFICATION: hangi aralık?]"),
        )
        self.assertRejects(
            "SPEC_CLARIFICATION_UNRESOLVED",
            specification(requirements=["Yetki [NEEDS CLARIFICATION: hangi roller?]"]),
        )

    def test_root_and_required_fields(self) -> None:
        for payload in ([], "spec", 7, None):
            self.assertRejects("SPEC_ROOT_INVALID", payload)
        self.assertRejects("SPEC_FERMAN_REQUIRED", specification(ferman="  "))
        self.assertRejects("SPEC_OUTCOME_REQUIRED", specification(outcome=None))

    def test_stories_must_be_usable(self) -> None:
        self.assertRejects("SPEC_STORIES_INVALID", specification(stories=[]))
        self.assertRejects("SPEC_STORY_INVALID", specification(stories=["assign"]))
        self.assertRejects(
            "SPEC_STORY_PRIORITY_INVALID",
            specification(
                stories=[
                    {"id": "a", "title": "A", "priority": "P9", "narrative": "n", "acceptance": ["x"]}
                ]
            ),
        )
        self.assertRejects(
            "SPEC_STORY_ID_DUPLICATE",
            specification(
                stories=[
                    {"id": "a", "title": "A", "priority": "P1", "narrative": "n", "acceptance": ["x"]},
                    {"id": "a", "title": "B", "priority": "P1", "narrative": "n", "acceptance": ["x"]},
                ]
            ),
        )
        # A story with no acceptance criterion cannot be verified, so it cannot compile.
        self.assertRejects(
            "SPEC_TEXT_LIST_EMPTY",
            specification(
                stories=[
                    {"id": "a", "title": "A", "priority": "P1", "narrative": "n", "acceptance": []}
                ]
            ),
        )

    def test_quality_profile_must_be_known(self) -> None:
        for bad in ("CUSTOM", "", None, 5):
            self.assertRejects("SPEC_QUALITY_PROFILE_INVALID", specification(quality_profile=bad))

    def test_measurable_outcomes_are_mandatory(self) -> None:
        self.assertRejects("SPEC_TEXT_LIST_EMPTY", specification(measurable_outcomes=[]))
        self.assertRejects("SPEC_TEXT_LIST_INVALID", specification(measurable_outcomes="hızlı"))

    def test_architecture_decisions_are_optional_but_validated(self) -> None:
        self.assertTrue(compile_specification(specification()).ok)
        self.assertRejects(
            "SPEC_DECISION_FIELD_INVALID",
            specification(architecture_decisions=[{"id": "adr-1", "title": "T"}]),
        )
        result = compile_specification(
            specification(
                architecture_decisions=[
                    {
                        "id": "adr-1",
                        "title": "Depolama",
                        "choice": "SQLite",
                        "rationale": "Tek kullanıcı, yerel kurulum.",
                        "alternatives": ["Postgres"],
                    }
                ]
            )
        )
        self.assertTrue(result.ok, [i.code for i in result.issues])
        assert result.specification is not None
        self.assertEqual(result.specification.architecture[0].decision_id, "adr-1")


if __name__ == "__main__":
    unittest.main()
