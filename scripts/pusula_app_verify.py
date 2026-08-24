from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "incubator" / "pusula" / "backend"


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=BACKEND, env=os.environ.copy(), check=True)


def main() -> int:
    run("manage.py", "check")
    run("manage.py", "makemigrations", "--check", "--dry-run")
    run("manage.py", "migrate", "--noinput")
    run("manage.py", "test", "tests", "--verbosity", "2")
    print("PUSULA APP VERIFY VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
