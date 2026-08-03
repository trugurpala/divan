from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "divan_host_state", ROOT / "scripts" / "host_state.py"
)
assert SPEC and SPEC.loader
HOST_STATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST_STATE)


VERSIONS = {
    "sadrazam": "0.10.0",
    "core-pack": "0.5.1",
    "ui-pack": "0.2.0",
    "react-pack": "0.2.1",
    "zanaat-pack": "0.1.1",
}


def _run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def _normalize_git_source(value: str) -> str:
    return value.strip().replace("\\", "/").removesuffix("/").removesuffix(".git")


def _write_marketplace(root: pathlib.Path) -> pathlib.Path:
    path = root / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    plugins = [
        {
            "name": name,
            "version": version,
            "source": {"source": "local", "path": f"./plugins/{name}"},
        }
        for name, version in VERSIONS.items()
    ]
    payload = {"name": "divan", "plugins": plugins}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _init_git_repo(root: pathlib.Path, *, commit_message: str = "init") -> None:
    root.mkdir(parents=True, exist_ok=True)
    _run(["git", "-C", str(root), "init", "--quiet"])
    _run(["git", "-C", str(root), "config", "user.email", "test@example.com"])
    _run(["git", "-C", str(root), "config", "user.name", "Divan Bot"])


def _git_commit(root: pathlib.Path, message: str, *, filename: str = "README.md") -> None:
    (root / filename).write_text(message + "\n", encoding="utf-8")
    _run(["git", "-C", str(root), "add", "."])
    _run(["git", "-C", str(root), "commit", "--quiet", "-m", message])


class HostStateCheckoutEvidenceTests(unittest.TestCase):
    def test_checkout_evidence_uses_remote_source_when_local_head_is_not_matching(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-state-") as temporary:
            temporary_root = pathlib.Path(temporary)

            source_work = temporary_root / "source"
            _init_git_repo(source_work)
            _write_marketplace(source_work)
            _git_commit(source_work, "source base")
            source_tag = "v0.12.0"
            _run(["git", "-C", str(source_work), "tag", source_tag])

            source_bare = temporary_root / "source-bare.git"
            _run([
                "git",
                "clone",
                "--bare",
                "--quiet",
                str(source_work),
                str(source_bare),
            ])

            caller = temporary_root / "caller"
            _init_git_repo(caller)
            (caller / "app.txt").write_text("caller", encoding="utf-8")
            _run(["git", "-C", str(caller), "add", "."])
            _run(["git", "-C", str(caller), "commit", "--quiet", "-m", "caller"])
            _run([
                "git",
                "-C",
                str(caller),
                "remote",
                "add",
                "origin",
                "https://github.com/example/other/divan.git",
            ])

            source = source_bare.as_uri()
            evidence = HOST_STATE.checkout_evidence(caller, source, source_tag, _run, _normalize_git_source)

            self.assertEqual(_normalize_git_source(evidence["source"]), _normalize_git_source(source))
            self.assertEqual(evidence["ref"], source_tag)
            self.assertEqual(evidence["contract"], VERSIONS)

            expected_digest = hashlib.sha256(_write_marketplace(source_work).read_bytes()).hexdigest()
            self.assertEqual(evidence["catalog_digest"], expected_digest)

    def test_checkout_evidence_rejects_remote_commit_ref_without_local_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-host-state-") as temporary:
            temporary_root = pathlib.Path(temporary)

            source_work = temporary_root / "source"
            _init_git_repo(source_work)
            _write_marketplace(source_work)
            _git_commit(source_work, "source base")
            source_sha = _run(["git", "-C", str(source_work), "rev-parse", "HEAD"])

            source_bare = temporary_root / "source-bare.git"
            _run([
                "git",
                "clone",
                "--bare",
                "--quiet",
                str(source_work),
                str(source_bare),
            ])

            caller = temporary_root / "caller"
            _init_git_repo(caller)
            with self.assertRaisesRegex(HOST_STATE.StateError, "cannot be proven"):
                HOST_STATE.checkout_evidence(
                    caller,
                    source_bare.as_uri(),
                    source_sha,
                    _run,
                    _normalize_git_source,
                )


if __name__ == "__main__":
    unittest.main()
