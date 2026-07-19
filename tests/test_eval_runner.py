from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("divan_evals", ROOT / "evals" / "run.py")
assert SPEC and SPEC.loader
EVALS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALS)


class EvalRunnerTests(unittest.TestCase):
    def test_adapter_protocol_uses_utf8_for_non_ascii_payloads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-utf8-fixture-") as temporary:
            adapter = pathlib.Path(temporary) / "adapter.py"
            adapter.write_text(
                "import json, sys; value=json.loads(sys.stdin.buffer.read().decode('utf-8')); "
                "print(json.dumps({'prompt': value['prompt']}, ensure_ascii=False))\n",
                encoding="utf-8",
            )

            result = EVALS._run_adapter(
                f'"{sys.executable}" "{adapter}"',
                {"prompt": "Türkçe bağlam"},
                10,
            )

        self.assertEqual(result["prompt"], "Türkçe bağlam")

    @unittest.skipUnless(os.name == "nt", "Windows command wrapper regression")
    def test_provider_version_supports_windows_cmd_wrappers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-version-fixture-") as temporary:
            command = pathlib.Path(temporary) / "provider.cmd"
            command.write_text("@echo off\r\necho provider 1.2.3\r\n", encoding="utf-8")
            path_value = str(command.parent) + os.pathsep + os.environ.get("PATH", "")
            with mock.patch.dict(
                os.environ,
                {"DIVAN_FIXTURE_BIN": "provider", "PATH": path_value},
            ):
                version = EVALS._version_for_command("DIVAN_FIXTURE_BIN", "missing")

        self.assertEqual(version, "provider 1.2.3")

    def test_discovers_current_contracts(self) -> None:
        cases = EVALS.discover_cases(ROOT)
        self.assertEqual(len(cases), 13)
        self.assertEqual(
            {case["skill_name"] for case in cases},
            {"arama-ustasi", "baglam-muhafizi", "kaynak-kuratori", "vezir-yetistirme"},
        )

    def test_zero_cases_is_not_success(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-empty-evals-") as temporary:
            with self.assertRaisesRegex(EVALS.EvalError, "sıfır eval"):
                EVALS.discover_cases(pathlib.Path(temporary))

    def test_first_party_provider_preset_is_available(self) -> None:
        args = EVALS.build_parser().parse_args(
            ["--run", "--provider-preset", "claude-codex", "--skill", "baglam-muhafizi"]
        )
        self.assertEqual(args.provider_preset, "claude-codex")

    def test_first_party_provider_rejects_tool_dependent_skill_contracts(self) -> None:
        with self.assertRaisesRegex(EVALS.EvalError, "non-tool"):
            EVALS._validate_provider_skill_scope({"arama-ustasi"})

    def test_provenance_is_bound_to_clean_repository_head(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-eval-git-") as temporary:
            root = pathlib.Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Fixture"], check=True
            )
            (root / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "VERSION"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
            head = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
            ).strip()

            identity = EVALS._repository_identity(root)
            self.assertEqual(identity, {"source_commit": head, "divan_version": "9.9.9"})

            (root / "VERSION").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(EVALS.EvalError, "clean"):
                EVALS._repository_identity(root)

    def test_blind_pair_judge_and_threshold(self) -> None:
        case = EVALS.discover_cases(ROOT, {"kaynak-kuratori"})[:1]
        with tempfile.TemporaryDirectory(prefix="divan-eval-adapter-") as temporary:
            temp = pathlib.Path(temporary)
            adapter = temp / "adapter.py"
            judge = temp / "judge.py"
            adapter.write_text(
                textwrap.dedent(
                    """
                    import json, sys
                    request = json.load(sys.stdin)
                    marker = "skill-kanitli" if request["condition"] == "skill" else "baseline"
                    print(json.dumps({"output": marker, "events": [], "changed_files": []}))
                    """
                ),
                encoding="utf-8",
            )
            judge.write_text(
                textwrap.dedent(
                    """
                    import json, sys
                    request = json.load(sys.stdin)
                    winner = next(label for label, value in request["candidates"].items() if "skill-kanitli" in value["output"])
                    print(json.dumps({"winner": winner, "reasons": ["rubrik"], "expectation_scores": {"rubrik": True}}))
                    """
                ),
                encoding="utf-8",
            )
            result, key = EVALS.run_evaluations(
                case,
                f"{sys.executable} {adapter}",
                f"{sys.executable} {judge}",
                min_skill_win_rate=1.0,
            )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["summary"]["skill_wins"], 1)
        self.assertTrue(result["summary"]["gate_passed"])
        self.assertNotIn("mapping", result["cases"][0])
        self.assertIn("mapping", key["cases"][0])
        self.assertNotIn("winner_condition", result["cases"][0]["judgement"])
        self.assertIn("winner_condition", key["cases"][0])

    def test_public_candidate_redacts_secrets_email_and_home_paths(self) -> None:
        result = EVALS._validate_agent_result(
            {
                "output": "token=super-secret user@example.com C:\\Users\\Pala\\private.txt",
                "events": ["api_key=abc123456789"],
                "changed_files": ["/home/pala/private.txt"],
            }
        )

        rendered = json.dumps(result)
        for secret in ("super-secret", "user@example.com", "Pala", "/home/pala"):
            self.assertNotIn(secret, rendered)
        self.assertIn("[REDACTED]", rendered)

    def test_without_judge_requires_review(self) -> None:
        case = EVALS.discover_cases(ROOT, {"arama-ustasi"})[:1]
        with tempfile.TemporaryDirectory(prefix="divan-eval-adapter-") as temporary:
            adapter = pathlib.Path(temporary) / "adapter.py"
            adapter.write_text(
                "import json, sys; json.load(sys.stdin); print(json.dumps({'output':'yanit','events':[],'changed_files':[]}))\n",
                encoding="utf-8",
            )
            result, _key = EVALS.run_evaluations(case, f"{sys.executable} {adapter}")
        self.assertEqual(result["status"], "review_required")
        self.assertIsNone(result["summary"]["skill_win_rate"])
        self.assertIsNone(result["summary"]["gate_passed"])

    def test_run_retains_valid_public_provenance(self) -> None:
        case = EVALS.discover_cases(ROOT, {"arama-ustasi"})[:1]
        provenance = {
            "agent": "Declared runner",
            "agent_version": "1.2.3",
            "judge": "Independent judge",
            "judge_version": "4.5.6",
            "source_commit": "0123456789abcdef",
            "environment": "Windows 11; redacted local environment",
        }
        with tempfile.TemporaryDirectory(prefix="divan-eval-provenance-") as temporary:
            adapter = pathlib.Path(temporary) / "adapter.py"
            adapter.write_text(
                "import json, sys; json.load(sys.stdin); print(json.dumps({'output':'yanit','events':[],'changed_files':[]}))\n",
                encoding="utf-8",
            )
            result, key = EVALS.run_evaluations(
                case,
                f"{sys.executable} {adapter}",
                provenance=provenance,
            )
        self.assertEqual(result["provenance"], provenance)
        self.assertNotIn("provenance", key)

    def test_read_provenance_rejects_missing_required_field(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-eval-provenance-") as temporary:
            path = pathlib.Path(temporary) / "provenance.json"
            path.write_text(
                json.dumps(
                    {
                        "agent": "Declared runner",
                        "agent_version": "1.2.3",
                        "judge": "Independent judge",
                        "source_commit": "0123456789abcdef",
                        "environment": "Windows 11",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EVALS.EvalError, "judge_version"):
                EVALS._read_provenance(path)

    def test_threshold_can_fail(self) -> None:
        case = EVALS.discover_cases(ROOT, {"baglam-muhafizi"})[:1]
        with tempfile.TemporaryDirectory(prefix="divan-eval-threshold-") as temporary:
            temp = pathlib.Path(temporary)
            adapter = temp / "adapter.py"
            judge = temp / "judge.py"
            adapter.write_text(
                textwrap.dedent(
                    """
                    import json, sys
                    request = json.load(sys.stdin)
                    print(json.dumps({"output": request["condition"], "events": [], "changed_files": []}))
                    """
                ),
                encoding="utf-8",
            )
            judge.write_text(
                textwrap.dedent(
                    """
                    import json, sys
                    request = json.load(sys.stdin)
                    winner = next(label for label, value in request["candidates"].items() if value["output"] == "baseline")
                    print(json.dumps({"winner": winner, "reasons": ["fixture"], "expectation_scores": {}}))
                    """
                ),
                encoding="utf-8",
            )
            result, _key = EVALS.run_evaluations(
                case,
                f"{sys.executable} {adapter}",
                f"{sys.executable} {judge}",
                min_skill_win_rate=0.5,
            )
        self.assertEqual(result["summary"]["baseline_wins"], 1)
        self.assertFalse(result["summary"]["gate_passed"])


if __name__ == "__main__":
    unittest.main()
