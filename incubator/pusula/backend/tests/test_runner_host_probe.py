from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pusula.integrations.runner.host_probe import probe_microvm_host


class RunnerHostProbeTests(unittest.TestCase):
    def _probe(self, *, role: str = "isolated-worker", control_plane: str = "0"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kvm = root / "kvm"
            cgroup = root / "cgroup.controllers"
            firecracker = root / "firecracker"
            jailer = root / "jailer"
            ip = root / "ip"
            kvm.write_bytes(b"kvm")
            cgroup.write_text("cpu memory pids")
            firecracker.write_bytes(b"firecracker-binary")
            jailer.write_bytes(b"jailer-binary")
            ip.write_bytes(b"ip-binary")

            paths = {
                "firecracker": str(firecracker),
                "jailer": str(jailer),
                "ip": str(ip),
            }
            with patch(
                "pusula.integrations.runner.host_probe.shutil.which",
                side_effect=lambda name: paths.get(name),
            ):
                return probe_microvm_host(
                    environ={
                        "PUSULA_RUNNER_ROLE": role,
                        "PUSULA_CONTROL_PLANE": control_plane,
                    },
                    kvm_path=str(kvm),
                    cgroup_controllers_path=str(cgroup),
                )

    def test_complete_probe_is_ready_and_hashes_binaries(self) -> None:
        facts = self._probe()
        self.assertTrue(facts.ready_for_untrusted)
        self.assertEqual(
            facts.firecracker_sha256,
            hashlib.sha256(b"firecracker-binary").hexdigest(),
        )
        self.assertEqual(
            facts.jailer_sha256,
            hashlib.sha256(b"jailer-binary").hexdigest(),
        )

    def test_missing_worker_role_blocks_untrusted(self) -> None:
        facts = self._probe(role="web")
        self.assertFalse(facts.ready_for_untrusted)
        self.assertIn("not_dedicated_worker", facts.blocking_reasons())

    def test_control_plane_marker_blocks_even_dedicated_worker(self) -> None:
        facts = self._probe(control_plane="true")
        self.assertFalse(facts.ready_for_untrusted)
        self.assertIn("control_plane_host_forbidden", facts.blocking_reasons())

    def test_missing_binary_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kvm = root / "kvm"
            cgroup = root / "cgroup.controllers"
            kvm.write_bytes(b"kvm")
            cgroup.write_text("cpu memory pids")
            with patch(
                "pusula.integrations.runner.host_probe.shutil.which",
                return_value=None,
            ):
                facts = probe_microvm_host(
                    environ={"PUSULA_RUNNER_ROLE": "isolated-worker"},
                    kvm_path=str(kvm),
                    cgroup_controllers_path=str(cgroup),
                )
        self.assertFalse(facts.ready_for_untrusted)
        self.assertIn("firecracker_unverified", facts.blocking_reasons())
        self.assertIn("jailer_unverified", facts.blocking_reasons())
        self.assertIn("network_namespace_unavailable", facts.blocking_reasons())
