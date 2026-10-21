import hashlib
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.isolated_check import (
    PROCESS_REAP_TIMEOUT, TREE_TERMINATION_TIMEOUT, IsolatedCheckError, check_ref,
)


class IsolatedCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-isolation-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.write(".gitignore", ".local/\n")
        self.write("tracked.txt", "committed\n")
        self.write("scripts/divan_v2_validate.py", "print('fixture validator passed')\n")
        self.write("scripts/package_divan_v2.py", "from pathlib import Path\nPath('dist').mkdir()\nPath('dist/fixture.zip').write_bytes(b'fixture package')\n")
        self.write("tests/test_fixture.py", "import unittest\nclass Fixture(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")
        self.commit()

    def git(self, *arguments):
        environment = dict(os.environ)
        environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        result = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "-c", f"core.hooksPath={self.repo / 'unused-hooks'}", "-C", str(self.repo), *arguments],
            env=environment,
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        return result.stdout.strip()

    def write(self, relative, text):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Isolation Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")

    def test_runs_exact_ref_without_dirty_files_or_inherited_secrets(self):
        self.write("scripts/divan_v2_validate.py", """import os
from pathlib import Path
assert Path('tracked.txt').read_text() == 'committed\\n'
assert not Path('.local/secret.txt').exists()
assert not Path('untracked.txt').exists()
assert 'DIVAN_TEST_SECRET' not in os.environ
assert not Path('.git').exists()
assert Path(os.environ['CODEX_HOME']).is_dir()
Path('tracked.txt').write_text('changed only in snapshot')
print('isolated fixture passed')
""")
        self.commit()
        commit = self.git("rev-parse", "HEAD")
        tree = self.git("rev-parse", "HEAD^{tree}")
        self.write("tracked.txt", "local edits\n")
        self.write("untracked.txt", "not part of revision\n")
        self.write(".local/secret.txt", "private fixture\n")
        before = self.git("status", "--porcelain")

        with patch.dict(os.environ, {"DIVAN_TEST_SECRET": "must-not-cross-boundary"}):
            report = check_ref(self.repo, commit)

        self.assertTrue(report["success"], report)
        self.assertEqual(report["object_sha"], commit)
        self.assertEqual(report["tree_sha"], tree)
        self.assertFalse(report["working_tree_included"])
        self.assertEqual(len(report["checks"]), 3)
        self.assertEqual(report["packages"][0]["sha256"], hashlib.sha256(b"fixture package").hexdigest())
        self.assertEqual((self.repo / "tracked.txt").read_text(), "local edits\n")
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertFalse((self.repo / "dist").exists())

    def test_failed_validation_stops_before_tests_and_package(self):
        self.write("scripts/divan_v2_validate.py", "print('deliberate validation failure')\nraise SystemExit(7)\n")
        self.commit()

        report = check_ref(self.repo)

        self.assertFalse(report["success"])
        self.assertEqual(len(report["checks"]), 1)
        self.assertEqual(report["checks"][0]["returncode"], 7)
        self.assertIn("deliberate validation failure", report["checks"][0]["output"])
        self.assertEqual(report["packages"], [])

    def test_missing_ref_is_an_error_without_source_changes(self):
        before = self.git("status", "--porcelain")
        with self.assertRaisesRegex(IsolatedCheckError, "resolve"):
            check_ref(self.repo, "refs/heads/does-not-exist")
        self.assertEqual(self.git("status", "--porcelain"), before)

    def test_rejects_symlink_blob_even_on_windows_without_symlink_privilege(self):
        blob = self.git("hash-object", "-w", "tracked.txt")
        self.git("update-index", "--add", "--cacheinfo", f"120000,{blob},linked.txt")
        tree = self.git("write-tree")

        with self.assertRaisesRegex(IsolatedCheckError, "symlink|regular file"):
            check_ref(self.repo, tree)

    def test_export_attributes_cannot_silently_omit_tracked_content(self):
        self.write(".gitattributes", "tracked.txt export-ignore\n")
        self.commit()

        with self.assertRaisesRegex(IsolatedCheckError, "archive.*tree|tracked.*archive"):
            check_ref(self.repo)

    def test_timeout_is_reported_as_failure(self):
        self.write("scripts/divan_v2_validate.py", "import time\ntime.sleep(30)\n")
        self.commit()

        report = check_ref(self.repo, timeout=0.2)

        self.assertFalse(report["success"])
        self.assertTrue(report["checks"][0]["timed_out"])
        self.assertEqual(len(report["checks"]), 1)

    def test_timeout_terminates_child_process_before_it_can_write(self):
        timeout = 0.3
        cleanup_budget = TREE_TERMINATION_TIMEOUT + PROCESS_REAP_TIMEOUT
        maximum_duration = timeout + cleanup_budget + 1  # scheduler allowance
        child_delay = maximum_duration + 2
        marker = Path(self.temporary.name) / "orphan-wrote.txt"
        child_code = (
            "import time; from pathlib import Path; "
            f"time.sleep({child_delay}); Path({str(marker)!r}).write_text('orphan survived')"
        )
        self.write("scripts/divan_v2_validate.py", (
            "import subprocess, sys, time\n"
            f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
            "print('child started', flush=True)\n"
            f"time.sleep({child_delay + 10})\n"
        ))
        self.commit()

        report = check_ref(self.repo, timeout=timeout)

        elapsed = report["checks"][0]["seconds"]
        self.assertTrue(report["checks"][0]["timed_out"])
        self.assertIn("child started", report["checks"][0]["output"])
        # Snapshot export and verification precede the command deadline and can
        # be slower on a loaded Windows host; measure only the timed command.
        with self.subTest("bounded cleanup"):
            self.assertLess(elapsed, maximum_duration, "inherited stdout must not defeat the bounded cleanup deadline")
        # Check after the full cleanup deadline: Windows taskkill startup can
        # take several seconds with a fresh profile. A surviving child would
        # write after this deadline even if only its direct parent was killed.
        time.sleep(max(0, child_delay + 0.4 - elapsed))
        with self.subTest("no orphan writes"):
            self.assertFalse(marker.exists(), "timed-out command left a child process running")


if __name__ == "__main__":
    unittest.main()
