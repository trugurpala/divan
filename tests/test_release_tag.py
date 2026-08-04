from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "divan_release_tag", ROOT / "scripts" / "release_tag.py"
)
assert SPEC and SPEC.loader
RELEASE_TAG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE_TAG)


class ReleaseTagTests(unittest.TestCase):
    def _run(self, *command: str) -> None:
        subprocess.run(
            list(command),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def _repository(self, base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, str]:
        source = base / "source checkout"
        remote = base / "bare remote.git"
        source.mkdir()
        self._run("git", "init", "--quiet", str(source))
        self._run("git", "-C", str(source), "config", "user.name", "Divan Test")
        self._run(
            "git",
            "-C",
            str(source),
            "config",
            "user.email",
            "divan-test@example.invalid",
        )
        (source / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        self._run("git", "-C", str(source), "add", "VERSION")
        self._run("git", "-C", str(source), "commit", "--quiet", "-m", "fixture")
        self._run("git", "init", "--bare", "--quiet", str(remote))
        self._run("git", "-C", str(source), "remote", "add", "origin", str(remote))
        self._run("git", "-C", str(source), "push", "--quiet", "origin", "HEAD:main")
        commit = subprocess.check_output(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
        ).strip()
        return source, remote, commit

    def test_resolves_absent_lightweight_and_annotated_remote_tags(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-release-tag-") as temporary:
            source, remote, commit = self._repository(pathlib.Path(temporary))

            self.assertIsNone(
                RELEASE_TAG.resolve_remote_tag(str(remote), "v9.9.6")
            )

            self._run("git", "-C", str(source), "tag", "v9.9.7")
            self._run(
                "git",
                "-C",
                str(source),
                "push",
                "--quiet",
                "origin",
                "refs/tags/v9.9.7",
            )
            self.assertEqual(
                RELEASE_TAG.resolve_remote_tag(str(remote), "v9.9.7"),
                commit,
            )

            self._run(
                "git",
                "-C",
                str(source),
                "tag",
                "-a",
                "v9.9.8",
                "-m",
                "annotated fixture",
            )
            self._run(
                "git",
                "-C",
                str(source),
                "push",
                "--quiet",
                "origin",
                "refs/tags/v9.9.8",
            )
            self.assertEqual(
                RELEASE_TAG.resolve_remote_tag(str(remote), "v9.9.8"),
                commit,
            )

    def test_rejects_invalid_tag_and_malformed_remote_response(self) -> None:
        with self.assertRaisesRegex(
            RELEASE_TAG.ReleaseTagError, "SemVer"
        ):
            RELEASE_TAG.resolve_remote_tag("origin", "latest")

        def malformed(_command: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                [],
                0,
                "not-a-sha refs/tags/v1.2.3\n",
                "",
            )

        with self.assertRaisesRegex(
            RELEASE_TAG.ReleaseTagError, "response is invalid"
        ):
            RELEASE_TAG.resolve_remote_tag(
                "origin",
                "v1.2.3",
                run=malformed,
            )

    def test_redacts_git_stderr_when_remote_lookup_fails(self) -> None:
        secret = "ghp_SUPERSECRET"
        remote = f"https://alice:{secret}@example.invalid/repo.git"

        def failed(_command: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                [],
                128,
                "",
                f"fatal: unable to access '{remote}/': authentication failed",
            )

        with self.assertRaises(RELEASE_TAG.ReleaseTagError) as caught:
            RELEASE_TAG.resolve_remote_tag(
                remote,
                "v1.2.3",
                run=failed,
            )

        message = str(caught.exception)
        self.assertEqual(
            message,
            "cannot read remote release tag "
            "(git ls-remote exited with status 128)",
        )
        self.assertNotIn("alice", message)
        self.assertNotIn(secret, message)
        self.assertNotIn(remote, message)


if __name__ == "__main__":
    unittest.main()
