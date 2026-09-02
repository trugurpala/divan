import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_SKILLS = {"divan","repo-audit","implementation-plan","root-cause-debug","quality-review","completion-proof","project-contract"}

class DivanV2EvalContractTests(unittest.TestCase):
    def test_eval_contract_has_review_minimums_and_valid_skill_targets(self):
        payload=json.loads((ROOT/"evals"/"divan-v2-routing.json").read_text(encoding="utf-8")); positive=payload["positive"]; negative=payload["negative"]
        self.assertGreaterEqual(len(positive),5); self.assertGreaterEqual(len(negative),3); ids=set()
        for case in positive+negative:
            self.assertNotIn(case["id"],ids); ids.add(case["id"]); self.assertTrue(case["prompt"].strip()); self.assertTrue(case["expected"].strip())
            for skill in case.get("skills",[]): self.assertIn(skill,VALID_SKILLS)
        self.assertTrue(any(case.get("skills")==["completion-proof"] and "test etmeden" in case["prompt"].casefold() for case in negative),"negative evals must include resistance to an unsupported completion claim")

if __name__ == "__main__": unittest.main()
