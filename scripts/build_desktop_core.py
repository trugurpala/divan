#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "divan-desktop-bridge.py"
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
BUILD_ROOT = ROOT / "build" / "desktop-core"
DIST = BUILD_ROOT / "dist"
WORK = BUILD_ROOT / "work"
SPEC = BUILD_ROOT / "spec"
BINARIES = ROOT / "apps" / "desktop" / "src-tauri" / "binaries"


def target_triple() -> str:
    completed = subprocess.run(
        ["rustc", "--print", "host-tuple"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    value = completed.stdout.strip()
    if not value:
        raise RuntimeError("rustc returned an empty host tuple")
    return value


def main() -> int:
    if not ENTRY.exists():
        raise FileNotFoundError(ENTRY)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    BINARIES.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "divan-core",
            "--paths",
            str(PLUGIN_ROOT),
            "--distpath",
            str(DIST),
            "--workpath",
            str(WORK),
            "--specpath",
            str(SPEC),
            str(ENTRY),
        ],
        cwd=ROOT,
        check=True,
    )

    extension = ".exe" if sys.platform == "win32" else ""
    source = DIST / f"divan-core{extension}"
    destination = BINARIES / f"divan-core-{target_triple()}{extension}"
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, destination)
    print(destination.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
