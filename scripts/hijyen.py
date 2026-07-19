#!/usr/bin/env python3
"""Divan repo hijyeni: UTF-8 metin ve güvenli üretilmiş-artefakt kapısı."""

from __future__ import annotations

import argparse
import ast
import pathlib
import shutil
import subprocess
import sys
from collections.abc import Iterable

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED_DIRECTORIES = frozenset(
    {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "htmlcov"}
)
EXCLUDED_TREES = frozenset({".git", ".worktrees"})
TEXT_SUFFIXES = frozenset(
    {
        ".cjs",
        ".css",
        ".csv",
        ".dot",
        ".html",
        ".js",
        ".json",
        ".md",
        ".mjs",
        ".ps1",
        ".py",
        ".sh",
        ".toml",
        ".ts",
        ".tsv",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)
TEXT_NAMES = frozenset({"AGENTS.md", "CLAUDE.md", "LICENSE", "VERSION"})
FIRST_PARTY_EXCLUDES = frozenset({"plugins"})
MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u00c3",
    "\u00c2",
    "\u00e2\u20ac",
    "\u00c4\u00b1",
    "\u00c4\u0178",
    "\u00c5\u0178",
)


def _relative(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def _is_text(path: pathlib.Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES


def first_party_text_paths(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    """Return tracked first-party text paths, with a filesystem fallback for fixtures."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        candidates = [root / item for item in completed.stdout.split("\0") if item]
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        candidates = [path for path in root.rglob("*") if path.is_file()]
    return sorted(
        path
        for path in candidates
        if path.is_file()
        and _is_text(path)
        and path.relative_to(root).parts[0] not in FIRST_PARTY_EXCLUDES | EXCLUDED_TREES
    )


def text_issues(
    root: pathlib.Path = ROOT, paths: Iterable[pathlib.Path] | None = None
) -> list[str]:
    """Report invalid UTF-8, BOM and common double-decoding signatures."""
    issues: list[str] = []
    for path in paths if paths is not None else first_party_text_paths(root):
        label = _relative(path, root)
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            issues.append(f"{label}: UTF-8 değil ({error})")
            continue
        if text.startswith("\ufeff"):
            issues.append(f"{label}: UTF-8 BOM içeriyor")
        if any(marker in text for marker in MOJIBAKE_MARKERS):
            issues.append(f"{label}: olası mojibake karakter dizisi içeriyor")
    return issues


def subprocess_encoding_issues(root: pathlib.Path = ROOT) -> list[str]:
    """Find locale-dependent text subprocess calls in first-party runtime code."""
    issues: list[str] = []
    sources = sorted(
        path
        for directory in (root / "scripts", root / "evals")
        if directory.is_dir()
        for path in directory.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"run", "check_output", "Popen"}:
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            text_mode = any(
                isinstance(value, ast.Constant) and value.value is True
                for value in (keywords.get("text"), keywords.get("universal_newlines"))
            )
            if text_mode and "encoding" not in keywords:
                issues.append(
                    f"{_relative(path, root)}:{node.lineno}: "
                    "text subprocess encoding='utf-8' ister"
                )
    return issues


def find_generated(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    """Find only allowlisted, reproducible artifacts without entering worktrees."""
    found: list[pathlib.Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_TREES for part in relative.parts):
            continue
        if path.is_dir() and path.name in GENERATED_DIRECTORIES:
            found.append(path)
        elif path.is_file() and path.name == ".coverage":
            found.append(path)
    roots: list[pathlib.Path] = []
    for path in sorted(found, key=lambda item: (len(item.parts), item.as_posix())):
        if not any(parent in roots for parent in path.parents):
            roots.append(path)
    return roots


def clean_generated(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    """Permanently delete allowlisted artifacts; refuse paths escaping root."""
    resolved_root = root.resolve()
    removed: list[pathlib.Path] = []
    for path in find_generated(root):
        if not path.resolve().is_relative_to(resolved_root):
            raise ValueError(f"güvenli kök dışına çıkan artefakt reddedildi: {path}")
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        removed.append(path)
    return removed


def check(root: pathlib.Path = ROOT) -> list[str]:
    issues = text_issues(root)
    issues.extend(subprocess_encoding_issues(root))
    issues.extend(
        f"{_relative(path, root)}: yeniden üretilebilir artefakt; --clean ile kaldır"
        for path in find_generated(root)
    )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--clean", action="store_true")
    args = parser.parse_args(argv)

    if args.clean:
        for path in clean_generated():
            print(f"SİLİNDİ: {_relative(path, ROOT)}")
    issues = check()
    if issues:
        print("HİJYEN BAŞARISIZ:")
        for issue in issues:
            print(f"  X {issue}")
        return 1
    print("HİJYEN TEMİZ — UTF-8/LF metin ve üretilmiş artefakt kapısı geçti")
    return 0


if __name__ == "__main__":
    sys.exit(main())
