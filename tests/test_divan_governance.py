from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import governance  # noqa: E402


class DivanGovernanceTests(unittest.TestCase):
    def test_owner_authority_binds_operation_and_scope(self) -> None:
        first = governance.authorize_mutation(
            "owner",
            "goal.start",
            {"intent": "Ship safely", "target": "verified"},
            explicit_authority=True,
            directory=RUNTIME,
        )
        second = governance.authorize_mutation(
            "owner",
            "goal.start",
            {"target": "verified", "intent": "Ship safely"},
            explicit_authority=True,
            directory=RUNTIME,
        )

        self.assertEqual(first, second)
        self.assertEqual(first["actor_id"], "owner")
        self.assertEqual(first["identity_boundary"], "host_os_account")
        self.assertRegex(first["mandate_id"], r"^mandate-[0-9a-f]{16}$")

    def test_delegated_actor_cannot_authorize_cli_mutation(self) -> None:
        with self.assertRaisesRegex(ValueError, "only owner/Hükümdar"):
            governance.authorize_mutation(
                "specialist",
                "project.update",
                {"project": "."},
                explicit_authority=True,
                directory=RUNTIME,
            )

    def test_execute_rejects_non_owner_before_project_mutation(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME / "cli.py"),
                "init",
                "--project",
                str(ROOT),
                "--actor",
                "provider",
                "--execute",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("only owner/Hükümdar", payload["errors"][0])


if __name__ == "__main__":
    unittest.main()
