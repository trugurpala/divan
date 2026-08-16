from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / ".github" / "workflows" / "desktop-build.yml"
LIFECYCLE = ROOT / "scripts" / "windows_desktop_lifecycle.ps1"
DESKTOP_STATE = ROOT / "plugins" / "sadrazam" / "divan_runtime" / "desktop_state.py"


class DesktopLifecycleContractTests(unittest.TestCase):
    def test_persistent_state_is_separate_from_product_named_installer_root(self) -> None:
        state = DESKTOP_STATE.read_text(encoding="utf-8")
        self.assertIn('WINDOWS_DATA_DIRECTORY = "com.ugurpala.ottoman"', state)
        self.assertNotIn('return Path(local_app_data) / "Ottoman"', state)

    def test_windows_build_runs_installed_lifecycle_matrix_and_uninstall(self) -> None:
        workflow = BUILD.read_text(encoding="utf-8")
        self.assertIn("windows_desktop_lifecycle.ps1", workflow)
        self.assertIn(
            "Verify Windows first-run matrix, crash recovery and Desktop restart persistence",
            workflow,
        )
        self.assertIn("schema_version -ne 2", workflow)
        self.assertIn("recovered_state -ne \"retry\"", workflow)
        self.assertIn("retry_without_approval_rejected", workflow)
        self.assertIn("recovery_evidence_sha256", workflow)
        self.assertIn("Uninstall and verify application removal with Core state preservation", workflow)
        self.assertIn("DIVAN_PERSISTENT_STATE_FILE", workflow)
        self.assertIn("com.ugurpala.ottoman/tasks/DIV-UNINSTALL-PRESERVE.json", workflow)
        self.assertIn("divan-desktop-windows-lifecycle", workflow)

    def test_lifecycle_matrix_uses_core_truth_for_restart_crash_and_orca_cases(self) -> None:
        script = LIFECYCLE.read_text(encoding="utf-8")
        self.assertIn('command = "project.register"', script)
        self.assertIn('command = "task.create"', script)
        self.assertIn('command = "task.plan"', script)
        self.assertIn('command = "task.list"', script)
        self.assertIn('command = "project.list"', script)
        self.assertIn("Invoke-DesktopRestart -Attempt 1", script)
        self.assertIn("Invoke-DesktopRestart -Attempt 2", script)

        self.assertIn('command = "task.start"', script)
        self.assertIn("approve_execution = $true", script)
        self.assertIn("execution_pending", script)
        self.assertIn("function Get-OptionalProperty", script)
        self.assertIn(
            'Get-OptionalProperty -Object $recovered.metadata -Name "execution_pending"',
            script,
        )
        self.assertNotIn("$recovered.metadata.execution_pending", script)
        self.assertIn("taskkill.exe /PID", script)
        self.assertIn('command = "task.recover.interrupted"', script)
        self.assertIn('command = "evidence.list"', script)
        self.assertIn('kind -eq "recovery"', script)
        self.assertIn("DESKTOP_EXECUTION_APPROVAL_REQUIRED", script)
        self.assertIn("retry_without_approval_rejected = $true", script)
        self.assertIn("mandate_preserved_across_recovery", script)
        self.assertNotIn('command = "task.approve"', script)
        self.assertNotIn('command = "task.merge"', script)

        self.assertIn('command = "readiness"', script)
        self.assertIn('"orca.cmd"', script)
        self.assertIn('command = "capabilities"', script)
        self.assertIn('"mandate-gate"', script)
        self.assertIn('"approval-gate"', script)
        self.assertIn("source_commit = $expectedCommit", script)
        self.assertIn("source_tree = $expectedTree", script)


if __name__ == "__main__":
    unittest.main()
