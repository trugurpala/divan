from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class RunnerProbeCliTests(unittest.TestCase):
    def test_control_plane_probe_is_machine_readable_and_blocked(self) -> None:
        backend = Path(__file__).resolve().parents[1]
        root = backend.parents[2]
        script = root / "scripts" / "pusula_runner_probe.py"
        env = os.environ.copy()
        env["PUSULA_RUNNER_ROLE"] = "isolated-worker"
        env["PUSULA_CONTROL_PLANE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema"], "pusula.runner-host-facts.v1")
        self.assertFalse(payload["eligible_for_untrusted"])
        self.assertIn("control_plane_host_forbidden", payload["blocking_reasons"])
