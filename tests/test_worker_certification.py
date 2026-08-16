from __future__ import annotations

import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import worker_certification as certification
from divan_runtime.worker_certification import AuthState, certify_worker
from divan_runtime.worker_discovery import WorkerFinding, WorkerProbe


def resolved(worker_id: str = "codex") -> WorkerProbe:
    return WorkerProbe(
        worker_id=worker_id,
        finding=WorkerFinding.RESOLVED,
        executable=f"C:/tools/{worker_id}.cmd",
    )


class _Result:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class CertificationTests(unittest.TestCase):
    def _run(self, version: str | None, auth_output: str):
        def fake(argv):
            if argv[-1] == "--version":
                return None if version is None else _Result(stdout=version)
            return _Result(stdout=auth_output)

        return patch.object(certification, "_run", side_effect=fake)

    def test_an_authenticated_worker_with_a_version_is_certified(self) -> None:
        with self._run("codex-cli 0.147.0", "Logged in using ChatGPT"):
            cert = certify_worker("codex", probe=resolved())

        self.assertTrue(cert.certified)
        self.assertEqual(cert.auth, AuthState.AUTHENTICATED)
        self.assertEqual(cert.version, "codex-cli 0.147.0")

    def test_a_signed_out_worker_is_never_certified(self) -> None:
        with self._run("2.1.229 (Claude Code)", "- Not signed in to claude.ai"):
            cert = certify_worker("claude", probe=resolved("claude"))

        self.assertFalse(cert.certified)
        self.assertEqual(cert.auth, AuthState.NOT_AUTHENTICATED)
        # The version is still known; only the session is missing.
        self.assertEqual(cert.version, "2.1.229 (Claude Code)")

    def test_a_silent_cli_is_unknown_and_not_certified(self) -> None:
        with self._run("codex-cli 0.147.0", "no opinion here"):
            cert = certify_worker("codex", probe=resolved())

        self.assertEqual(cert.auth, AuthState.UNKNOWN)
        self.assertFalse(cert.certified)
        self.assertTrue(any("could not be read" in note for note in cert.notes))

    def test_a_launcher_without_a_version_is_not_certified(self) -> None:
        with self._run(None, "Logged in using ChatGPT"):
            cert = certify_worker("codex", probe=resolved())

        self.assertIsNone(cert.version)
        self.assertFalse(cert.certified)

    def test_an_unresolved_worker_is_reported_rather_than_probed(self) -> None:
        cert = certify_worker(
            "codex",
            probe=WorkerProbe(
                worker_id="codex",
                finding=WorkerFinding.ABSENT,
                detail="not found anywhere",
            ),
        )

        self.assertFalse(cert.certified)
        self.assertIsNone(cert.executable)
        self.assertEqual(cert.auth, AuthState.UNKNOWN)

    def test_signed_out_wins_over_a_stray_signed_in_phrase(self) -> None:
        # Output that mentions both must fail closed.
        with self._run("x 1.0", "You were logged in. Not signed in to claude.ai"):
            cert = certify_worker("claude", probe=resolved("claude"))

        self.assertEqual(cert.auth, AuthState.NOT_AUTHENTICATED)


class RealMachineCertificationTests(unittest.TestCase):
    def test_this_machine_agrees_with_the_doctor(self) -> None:
        import tempfile

        from divan_runtime.doctor_checks import build_report

        with tempfile.TemporaryDirectory() as directory:
            report = build_report(
                state_root=pathlib.Path(directory),
                knowledge_database=pathlib.Path(directory) / "k.sqlite3",
            )
        states = {c.capability_id: c.state.value for c in report.capabilities}

        for worker_id in ("codex", "claude"):
            cert = certify_worker(worker_id)
            if cert.certified:
                self.assertEqual(states[worker_id], "CERTIFIED", worker_id)
            else:
                self.assertNotEqual(states[worker_id], "CERTIFIED", worker_id)


if __name__ == "__main__":
    unittest.main()
