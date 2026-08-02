from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
VERIFY_CLAIM = (
    ROOT
    / "plugins"
    / "react-pack"
    / "skills"
    / "vercel-optimize"
    / "lib"
    / "verify-claim.mjs"
)
COST_COVERAGE = VERIFY_CLAIM.with_name("cost-coverage.mjs")
RENDER_REPORT = VERIFY_CLAIM.with_name("render-report.mjs")
WORKSPACE_RESOLVER = VERIFY_CLAIM.with_name("workspace-resolver.mjs")
BRAINSTORM_SCRIPTS = (
    ROOT / "plugins" / "core-pack" / "skills" / "brainstorming" / "scripts"
)
ALGORITHMIC_VIEWER = (
    ROOT
    / "plugins"
    / "zanaat-pack"
    / "skills"
    / "algorithmic-art"
    / "templates"
    / "viewer.html"
)
P5_SRI = "sha384-Mhzoc5EVkjFUVtIW2M3h8BgXtFlUsUpu9lTCThPrV7+k6MN6vTi079rew0LkvgFb"


@unittest.skipUnless(NODE, "Node.js is required for distributed skill tests")
class DistributedSkillSecurityTests(unittest.TestCase):
    def run_node(self, source: str) -> str:
        completed = subprocess.run(
            [NODE, "--input-type=module", "-e", source],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip()

    def test_claim_patterns_are_literal_text_not_executable_regex(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-literal-pattern-") as temporary:
            root = pathlib.Path(temporary)
            (root / "sample.txt").write_text("aaaa", encoding="utf-8")
            source = f"""
import {{ verifyClaim }} from {json.dumps(VERIFY_CLAIM.as_uri())};
const result = await verifyClaim({{
  type: 'pattern_exists',
  repoRoot: {json.dumps(str(root))},
  file: 'sample.txt',
  pattern: '/a+/'
}});
console.log(JSON.stringify(result));
"""
            result = json.loads(self.run_node(source))

        self.assertEqual(result["disposition"], "failed")
        self.assertEqual(result["reason"], "pattern not found")

    def test_markdown_cells_escape_backslashes_before_pipes(self) -> None:
        source = f"""
import {{ renderCostCoverageMarkdown }} from {json.dumps(COST_COVERAGE.as_uri())};
import {{ renderReport }} from {json.dumps(RENDER_REPORT.as_uri())};
const hostile = 'a' + String.fromCharCode(92) + '|b' + String.fromCharCode(10) + 'c';
const cost = renderCostCoverageMarkdown({{
  totalBilled: 10,
  coveredBilled: 0,
  uncoveredBilled: 10,
  topGaps: [{{ name: hostile, billed: 10, share: 1, family: 'test' }}]
}}).find((line) => line.startsWith('| a'));
const report = renderReport({{
  recommendations: [{{ what: hostile, effort: 'low', bucket: 'quick', citations: [] }}]
}}).split(String.fromCharCode(10)).find((line) => line.startsWith('| 1 |'));
console.log(JSON.stringify({{ cost, report }}));
"""
        result = json.loads(self.run_node(source))
        escaped = "a" + "\\" * 3 + "|b c"

        self.assertIn(escaped, result["cost"])
        self.assertIn(escaped, result["report"])

    def test_workspace_export_replaces_every_target_star(self) -> None:
        source = f"""
import {{ buildResolver }} from {json.dumps(WORKSPACE_RESOLVER.as_uri())};
const resolve = buildResolver([{{
  name: 'example-package',
  dir: '/workspace/example-package',
  pkg: {{ exports: {{ './*': './src/*/*' }} }}
}}]);
console.log(JSON.stringify(resolve('example-package/widget')));
"""
        result = json.loads(self.run_node(source)).replace("\\", "/")

        self.assertTrue(result.endswith("/src/widget/widget"), result)

    def test_bootstrap_never_reflects_session_key_into_executable_html(self) -> None:
        server = (BRAINSTORM_SCRIPTS / "server.cjs").read_text(encoding="utf-8")
        helper = (BRAINSTORM_SCRIPTS / "helper.js").read_text(encoding="utf-8")

        self.assertIn("function bootstrapPage()", server)
        self.assertIn("res.end(bootstrapPage())", server)
        self.assertNotIn("sessionStorage", server)
        self.assertNotIn("brainstorm-session-key", helper)

    def test_remote_p5_script_has_pinned_subresource_integrity(self) -> None:
        viewer = ALGORITHMIC_VIEWER.read_text(encoding="utf-8")
        script_line = next(
            line for line in viewer.splitlines() if "cdnjs.cloudflare.com" in line
        )

        self.assertIn(f'integrity="{P5_SRI}"', script_line)
        self.assertIn('crossorigin="anonymous"', script_line)


if __name__ == "__main__":
    unittest.main()
