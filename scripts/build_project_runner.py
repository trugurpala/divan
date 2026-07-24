#!/usr/bin/env python3
"""Build the deterministic, stdlib-only Divan Project OS zipapp."""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_PATTERN = re.compile(r"[0-9a-f]{40}")
FILES = (
    "__init__.py",
    "adoption.py",
    "cli.py",
    "engine.py",
    "frameworks.json",
    "goal_archive.py",
    "goals.py",
    "impact-graph.json",
    "project_lifecycle.py",
    "project_os.py",
    "project_state.py",
    "project_transactions.py",
    "providers.py",
    "receipts.py",
    "roles.json",
    "workflows.json",
)
DATA_FILES = (
    ("data/seo-policy.json", "registry/seo-policy.json"),
)
ENTRYPOINT = (
    "import pathlib\n"
    "import sys\n"
    "import tempfile\n"
    "import zipfile\n"
    "\n"
    "if __name__ == \"__main__\":\n"
    "    with tempfile.TemporaryDirectory(prefix=\"divan-project-\") as directory:\n"
    "        with zipfile.ZipFile(pathlib.Path(sys.argv[0])) as archive:\n"
    "            archive.extractall(directory)\n"
    "        sys.path.insert(0, directory)\n"
    "        from cli import main\n"
    "        raise SystemExit(main())\n"
).encode("utf-8")


def _entry(name: str, content: bytes) -> tuple[str, bytes]:
    return name, content


def _write_entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def _verified_head(root: pathlib.Path, source_commit: str) -> None:
    if SOURCE_PATTERN.fullmatch(source_commit) is None:
        raise ValueError("source_commit must be a 40-character lowercase Git SHA")
    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            encoding="utf-8",
            errors="strict",
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ValueError("source root must be a readable Git repository") from error
    if status:
        raise ValueError("source repository must be clean")
    if head != source_commit:
        raise ValueError("source_commit must exactly match clean repository HEAD")


def build(output: pathlib.Path, source_commit: str, root: pathlib.Path = ROOT) -> None:
    root = root.resolve()
    _verified_head(root, source_commit)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    version_pattern = (
        r"(?:0|[1-9][0-9]*)\."
        r"(?:0|[1-9][0-9]*)\."
        r"(?:0|[1-9][0-9]*)"
    )
    if re.fullmatch(version_pattern, version) is None:
        raise ValueError("VERSION must contain canonical semantic version text")
    company = root / "plugins" / "sadrazam" / "company"
    entries = [_entry(name, (company / name).read_bytes()) for name in FILES]
    entries.extend(
        _entry(destination, (root / source).read_bytes())
        for destination, source in DATA_FILES
    )
    entries.extend(
        (
            _entry("__main__.py", ENTRYPOINT),
            _entry(
                "divan-project-source.json",
                (
                    json.dumps(
                        {
                            "schema_version": 2,
                            "source_commit": source_commit,
                            "source_ref": f"v{version}",
                            "source_repository": "https://github.com/trugurpala/divan",
                            "version": version,
                        },
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    + "\n"
                ).encode("utf-8"),
            ),
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for name, content in sorted(entries):
            _write_entry(archive, name, content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--source-commit", required=True)
    arguments = parser.parse_args()
    try:
        build(arguments.output, arguments.source_commit, arguments.root)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
