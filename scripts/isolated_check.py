"""Verify a fixed Git revision in a disposable workspace, using only stdlib + Git.

This isolates working files and inherited configuration, not operating-system
permissions or networking. Run it only on source you trust to execute locally.
Uncommitted/untracked files are excluded; pass a reviewed tree SHA to check an
index snapshot. The script never fetches, changes the source index, or installs.
The command timeout is followed by bounded cleanup: up to five seconds for tree
termination and five seconds to reap the direct process. It is not an exact
wall-clock deadline for exporting the Git snapshot or running cleanup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

TREE_TERMINATION_TIMEOUT = 5
PROCESS_REAP_TIMEOUT = 5


class IsolatedCheckError(RuntimeError):
    pass


def _terminate_tree(process: subprocess.Popen) -> None:
    """Kill only this check's process tree, then wait a bounded time to reap it."""
    try:
        if os.name == "nt":
            # Popen owns this PID. Taskkill /T targets its descendants as well;
            # /IM or a shell-built command could affect unrelated user processes.
            taskkill = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/taskkill.exe"
            stopped = subprocess.run(
                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=TREE_TERMINATION_TIMEOUT,
            )
            if stopped.returncode and process.poll() is None:
                raise IsolatedCheckError("could not terminate the timed-out check's process tree")
        else:
            # The check starts a new session, so the group contains its children
            # and cannot include this runner or unrelated terminal processes.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IsolatedCheckError(f"could not terminate the timed-out check's process tree: {exc}") from exc
    finally:
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=PROCESS_REAP_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            raise IsolatedCheckError("timed-out check did not terminate within the cleanup deadline") from exc


def _run_check(arguments: list[str], workspace: Path, env: dict[str, str], timeout: float) -> tuple[int | None, bytes, bool]:
    # A file avoids communicate() waiting indefinitely when a descendant inherits
    # a stdout pipe. Read only the bounded tail after the process tree is reaped.
    with tempfile.TemporaryFile(dir=workspace.parent) as output:
        process = subprocess.Popen(
            [sys.executable, *arguments], cwd=workspace, env=env,
            stdout=output, stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        timed_out = False
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out, returncode = True, None
            _terminate_tree(process)
        except BaseException:
            _terminate_tree(process)
            raise
        output.seek(0, os.SEEK_END)
        output.seek(max(0, output.tell() - 16000))
        return returncode, output.read(16000), timed_out


def _environment(root: Path) -> dict[str, str]:
    # An allowlist avoids forwarding API keys, Git credentials and MCP settings.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    for key, directory in {
        "HOME": "home", "USERPROFILE": "home", "CODEX_HOME": "codex",
        "APPDATA": "appdata", "LOCALAPPDATA": "localappdata",
        "XDG_CONFIG_HOME": "config", "XDG_CACHE_HOME": "cache",
        "TEMP": "tmp", "TMP": "tmp", "TMPDIR": "tmp",
    }.items():
        path = root / directory
        path.mkdir(exist_ok=True)
        env[key] = str(path)
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    return env


def _git(repo: Path, env: dict[str, str], *args: str) -> bytes:
    git = shutil.which("git", path=env.get("PATH", env.get("Path")))
    if not git:
        raise IsolatedCheckError("Git is required; no installation was attempted")
    try:
        result = subprocess.run(
            [git, "-C", str(repo), *args], env=env,
            capture_output=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IsolatedCheckError(f"Git operation failed: {exc}") from exc
    if result.returncode:
        raise IsolatedCheckError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _snapshot(repo: Path, ref: str, workspace: Path, env: dict[str, str]) -> tuple[str, str]:
    try:
        object_sha = _git(repo, env, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{object}}").decode().strip()
        tree_sha = _git(repo, env, "rev-parse", "--verify", f"{object_sha}^{{tree}}").decode().strip()
    except IsolatedCheckError as exc:
        raise IsolatedCheckError(f"cannot resolve Git revision {ref!r}: {exc}") from exc

    tracked: dict[str, str] = {}
    for entry in _git(repo, env, "ls-tree", "-r", "-z", "--full-tree", tree_sha).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        path = name.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise IsolatedCheckError(f"snapshot requires regular files (no symlink/submodule): {path}")
        tracked[path] = blob

    algorithm = _git(repo, env, "rev-parse", "--show-object-format").decode().strip()
    archive_path = workspace.parent / "source.tar"
    _git(repo, env, "archive", "--format=tar", f"--output={archive_path}", tree_sha)
    seen: set[str] = set()
    case_names: set[str] = set()
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            destination = workspace.joinpath(*relative.parts)
            if (
                relative.is_absolute() or ".." in relative.parts
                or PureWindowsPath(member.name).drive or "\\" in member.name
                or ":" in member.name or ".git" in relative.parts
                or not destination.resolve().is_relative_to(workspace)
            ):
                raise IsolatedCheckError(f"unsafe archive path: {member.name}")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or member.name not in tracked or member.name in seen:
                raise IsolatedCheckError(f"archive member does not match tracked regular file: {member.name}")
            if os.name == "nt" and member.name.casefold() in case_names:
                raise IsolatedCheckError(f"case-colliding archive path: {member.name}")
            case_names.add(member.name.casefold())
            stream = archive.extractfile(member)
            if stream is None:
                raise IsolatedCheckError(f"cannot read archive member: {member.name}")
            data = stream.read()
            blob_hash = hashlib.new(algorithm, f"blob {len(data)}\0".encode() + data).hexdigest()
            if blob_hash != tracked[member.name]:
                raise IsolatedCheckError(f"archive content differs from Git tree: {member.name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            if os.name != "nt":
                destination.chmod(member.mode & 0o777)
            seen.add(member.name)
    if seen != set(tracked):
        raise IsolatedCheckError("tracked files are missing from archive; export-ignore must not hide verification inputs")
    return object_sha, tree_sha


def check_ref(repo: Path, ref: str = "HEAD", *, timeout: float = 300) -> dict:
    """Return evidence; a nonzero check or timeout stops the sequence immediately."""
    if timeout <= 0:
        raise IsolatedCheckError("timeout must be positive")
    repo = repo.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="divan-isolated-") as temporary:
        root = Path(temporary).resolve()
        # Cleanup is limited to this freshly allocated absolute temporary root.
        if root.parent != Path(tempfile.gettempdir()).resolve() or root == repo or repo.is_relative_to(root):
            raise IsolatedCheckError("temporary workspace must be separate from the source repository")
        workspace = root / "source"
        workspace.mkdir()
        env = _environment(root)
        object_sha, tree_sha = _snapshot(repo, ref, workspace, env)
        report = {
            "success": False, "requested_ref": ref, "object_sha": object_sha, "tree_sha": tree_sha,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "platform": platform.system(),
            "working_tree_included": False,
            "scope": "Git snapshot; separate workspace/configuration; no OS or network sandbox; no model evaluation",
            "checks": [], "packages": [],
        }
        commands = [
            ("validate", ["scripts/divan_v2_validate.py"]),
            ("tests", ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]),
            ("package", ["scripts/package_divan_v2.py"]),
        ]
        for name, arguments in commands:
            started = time.monotonic()
            returncode, output, timed_out = _run_check(arguments, workspace, env, timeout)
            report["checks"].append({
                "name": name, "command": ["python", *arguments], "returncode": returncode,
                "timed_out": timed_out, "seconds": round(time.monotonic() - started, 3),
                "output": output.decode("utf-8", errors="replace")[-16000:],
            })
            if timed_out or returncode != 0:
                return report
        for package in sorted((workspace / "dist").glob("*.zip")):
            report["packages"].append({
                "name": package.name, "bytes": package.stat().st_size,
                "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
            })
        report["success"] = bool(report["packages"])
        if not report["success"]:
            report["error"] = "packaging exited successfully but produced no ZIP"
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--ref", default="HEAD", help="commit, tag, branch or reviewed tree SHA; excludes working-tree changes")
    parser.add_argument("--timeout", type=float, default=300, help="seconds per verification command; termination/reaping may add up to 10 seconds")
    args = parser.parse_args()
    try:
        report = check_ref(args.repo, args.ref, timeout=args.timeout)
    except (IsolatedCheckError, OSError, ValueError, tarfile.TarError) as exc:
        report = {"success": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
