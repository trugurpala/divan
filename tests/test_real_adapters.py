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
CLAUDE_ADAPTER = ROOT / "evals" / "adapters" / "claude_agent.py"
CODEX_JUDGE = ROOT / "evals" / "adapters" / "codex_judge.py"
COMMON_SPEC = importlib.util.spec_from_file_location(
    "divan_eval_adapter_common", ROOT / "evals" / "adapters" / "common.py"
)
assert COMMON_SPEC and COMMON_SPEC.loader
COMMON = importlib.util.module_from_spec(COMMON_SPEC)
COMMON_SPEC.loader.exec_module(COMMON)


class RealAdapterFixtureTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows command wrapper regression")
    def test_provider_cmd_wrapper_is_invokable_on_windows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-cmd-fixture-") as temporary:
            root = pathlib.Path(temporary)
            command = root / "provider.cmd"
            command.write_text("@echo off\r\necho fixture-provider\r\n", encoding="utf-8")

            path_value = str(root) + os.pathsep + os.environ.get("PATH", "")
            with mock.patch.dict(os.environ, {"PATH": path_value}):
                completed = COMMON.run_command(["provider"], cwd=root, timeout=5)

        self.assertEqual(completed.stdout.strip(), "fixture-provider")

    def _run_adapter(
        self, path: pathlib.Path, payload: dict, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            env=env,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )

    def test_claude_baseline_is_clean_and_treatment_loads_only_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-claude-fixture-") as temporary:
            temp = pathlib.Path(temporary)
            log = temp / "claude-argv.jsonl"
            fake = temp / "fake_claude.py"
            fake.write_text(
                textwrap.dedent(
                    """
                    import json, os, pathlib, sys
                    with pathlib.Path(os.environ["FIXTURE_LOG"]).open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(sys.argv[1:]) + "\\n")
                    print(json.dumps({"result": "fixture answer"}))
                    """
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update(
                {
                    "DIVAN_CLAUDE_BIN": f'"{sys.executable}" "{fake}"',
                    "FIXTURE_LOG": str(log),
                    "DIVAN_EVAL_TIMEOUT": "5",
                }
            )
            common = {
                "protocol_version": 1,
                "skill_name": "arama-ustasi",
                "case_id": 1,
                "prompt": "kanıtlı ara",
                "files": [],
            }
            baseline = self._run_adapter(
                CLAUDE_ADAPTER,
                {**common, "condition": "baseline", "skill_path": None},
                env,
            )
            treatment = self._run_adapter(
                CLAUDE_ADAPTER,
                {
                    **common,
                    "condition": "skill",
                    "skill_path": "plugins/core-pack/skills/arama-ustasi",
                },
                env,
            )

            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            self.assertEqual(treatment.returncode, 0, treatment.stderr)
            self.assertEqual(json.loads(baseline.stdout)["output"], "fixture answer")
            commands = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertNotIn("--plugin-dir", commands[0])
            self.assertIn("--plugin-dir", commands[1])
            plugin_dir = pathlib.Path(commands[1][commands[1].index("--plugin-dir") + 1])
            self.assertEqual(plugin_dir, ROOT / "plugins" / "core-pack")
            for command in commands:
                self.assertIn("--no-session-persistence", command)
                self.assertIn("--strict-mcp-config", command)
                self.assertEqual(
                    command[command.index("--mcp-config") + 1],
                    '{"mcpServers":{}}',
                )
                self.assertNotIn("--dangerously-skip-permissions", command)

    def test_codex_judge_is_read_only_structured_and_blinded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-codex-fixture-") as temporary:
            temp = pathlib.Path(temporary)
            log = temp / "judge.json"
            fake = temp / "fake_codex.py"
            fake.write_text(
                textwrap.dedent(
                    """
                    import json, os, pathlib, sys
                    args = sys.argv[1:]
                    prompt = sys.stdin.read()
                    pathlib.Path(os.environ["FIXTURE_LOG"]).write_text(
                        json.dumps({"args": args, "prompt": prompt}), encoding="utf-8"
                    )
                    output = pathlib.Path(args[args.index("--output-last-message") + 1])
                    output.write_text(json.dumps({
                        "winner": "A",
                        "reasons": ["fixture rubric"],
                        "expectation_scores": [{"expectation": "safe", "met": True}]
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update(
                {
                    "DIVAN_CODEX_BIN": f'"{sys.executable}" "{fake}"',
                    "FIXTURE_LOG": str(log),
                    "DIVAN_EVAL_TIMEOUT": "5",
                }
            )
            payload = {
                "protocol_version": 1,
                "skill_name": "arama-ustasi",
                "case_id": 1,
                "prompt": "kanıtlı ara",
                "expected_output": "kanıt",
                "expectations": ["safe"],
                "candidates": {
                    "A": {"output": "one", "events": [], "changed_files": []},
                    "B": {"output": "two", "events": [], "changed_files": []},
                },
            }

            result = self._run_adapter(CODEX_JUDGE, payload, env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["winner"], "A")
            self.assertEqual(
                json.loads(result.stdout)["expectation_scores"], {"safe": True}
            )
            invocation = json.loads(log.read_text(encoding="utf-8"))
            args = invocation["args"]
            self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
            self.assertIn("--ignore-user-config", args)
            self.assertIn("--ignore-rules", args)
            self.assertIn("--output-schema", args)
            self.assertIn("--disable", args)
            self.assertEqual(args[args.index("--disable") + 1], "plugins")
            self.assertNotIn("dangerously", " ".join(args))
            self.assertNotIn('"condition"', invocation["prompt"])
            self.assertNotIn('"mapping"', invocation["prompt"])

    def test_cli_failure_redacts_secret_like_stderr(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-secret-fixture-") as temporary:
            temp = pathlib.Path(temporary)
            fake = temp / "failing_claude.py"
            fake.write_text(
                "import sys; print('token sk-fixture-secret-value', file=sys.stderr); raise SystemExit(3)\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["DIVAN_CLAUDE_BIN"] = f'"{sys.executable}" "{fake}"'
            payload = {
                "protocol_version": 1,
                "condition": "baseline",
                "skill_name": "arama-ustasi",
                "case_id": 1,
                "prompt": "ara",
                "files": [],
                "skill_path": None,
            }

            result = self._run_adapter(CLAUDE_ADAPTER, payload, env)

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("sk-fixture-secret-value", result.stderr)
            self.assertIn("[REDACTED]", result.stderr)


if __name__ == "__main__":
    unittest.main()
