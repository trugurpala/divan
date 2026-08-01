#!/usr/bin/env python3
"""Check Divan's public prose for safe mechanical errors and review warnings."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC_ROOT_PATHS = (
    "README.md",
    "README.en.md",
    "README.tr.md",
    "BLUEPRINT.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.en.md",
    "CONTRIBUTING.tr.md",
    "SUPPORT.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "ROADMAP.md",
    "RELEASE.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "site/index.html",
    "docs/index.html",
)
PUBLIC_GLOBS = ("docs/*.md", ".github/ISSUE_TEMPLATE/*.yml")
MOJIBAKE = re.compile(
    "(?:T\\u00c3|\\u00c4[\\u00b1\\u0178\\u017e]|"
    "\\u00c5[\\u0178\\u017e]|\\u00c3[\\u00a7\\u00b6\\u00bc\\u2021\\u2013\\u0153]|"
    "\\u00e2\\u20ac|\\u00ef\\u00bb\\u00bf)"
)
MISSPELLINGS = re.compile(r"\b(?:herşey|birşey|yanlız|yada)\b", re.IGNORECASE)
PUNCTUATION_SPACE = re.compile(r"\s+[,;:!?](?=\s|$)")
REPEATED_SPACE = re.compile(r"\S[ \t]{2,}\S")
REPEATED_PUNCTUATION = re.compile(r"(?:!!+|\?\?+|,,+|;;+|::+)")
BROKEN_HEADING = re.compile(r"^#{1,6}[^#\s]", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
MARKETING = re.compile(
    r"\b(?:best[- ]in[- ]class|world[- ]class|premium quality|"
    r"adds value|delivers value|optimizes?\s+(?:your|the|every)|empowers?)\b",
    re.IGNORECASE,
)
PASSIVE_TR = re.compile(r"\b(?:edilmektedir|yapılmaktadır|sağlanmaktadır)\b", re.IGNORECASE)
TECHNICAL_DENSITY = re.compile(
    r"\b(?:runtime|orchestration|provenance|framework|workflow|schema|provider)\b",
    re.IGNORECASE,
)


class Finding(NamedTuple):
    level: str
    code: str
    path: str
    line: int
    message: str


class Report(NamedTuple):
    errors: tuple[Finding, ...]
    warnings: tuple[Finding, ...]


def public_files(root: pathlib.Path = ROOT) -> tuple[pathlib.Path, ...]:
    paths = {
        root / relative
        for relative in PUBLIC_ROOT_PATHS
        if (root / relative).is_file()
    }
    for pattern in PUBLIC_GLOBS:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    return tuple(sorted(paths, key=lambda path: path.relative_to(root).as_posix()))


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _finding(level: str, code: str, path: pathlib.Path, root: pathlib.Path, text: str, match: re.Match[str], message: str) -> Finding:
    return Finding(level, code, path.relative_to(root).as_posix(), _line_number(text, match.start()), message)


def _visible_lines(text: str):
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield number, line


def _relative_link_error(root: pathlib.Path, path: pathlib.Path, target: str) -> str | None:
    if target.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    clean = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not clean:
        return None
    resolved = (path.parent / clean).resolve()
    if not resolved.is_relative_to(root.resolve()):
        return "relative link leaves the repository"
    if not resolved.exists():
        return "relative Markdown link target does not exist"
    return None


def _prose_source(path: pathlib.Path, text: str) -> str:
    if path.suffix.casefold() != ".html":
        return text

    def preserve_lines(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        preserve_lines,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _inspect_file(root: pathlib.Path, path: pathlib.Path) -> tuple[list[Finding], list[Finding]]:
    text = path.read_text(encoding="utf-8")
    prose = _prose_source(path, text)
    errors: list[Finding] = []
    warnings: list[Finding] = []
    hard_rules = [
        (MOJIBAKE, "MOJIBAKE", "text contains likely UTF-8 corruption"),
        (MISSPELLINGS, "TR_SPELLING", "text contains a known unambiguous Turkish spelling error"),
        (PUNCTUATION_SPACE, "PUNCTUATION_SPACE", "remove the space before punctuation"),
        (REPEATED_SPACE, "REPEATED_SPACE", "text contains repeated horizontal spaces"),
        (REPEATED_PUNCTUATION, "REPEATED_PUNCTUATION", "text contains repeated punctuation"),
    ]
    if path.suffix.casefold() == ".md":
        hard_rules.append((BROKEN_HEADING, "MARKDOWN_HEADING", "Markdown heading needs a space after #"))
    for pattern, code, message in hard_rules:
        for match in pattern.finditer(prose):
            errors.append(_finding("error", code, path, root, prose, match, message))
    if path.suffix.casefold() == ".md":
        for match in MARKDOWN_LINK.finditer(text):
            message = _relative_link_error(root, path, match.group(1))
            if message:
                errors.append(_finding("error", "BROKEN_LINK", path, root, text, match, message))
    for line_number, line in _visible_lines(prose):
        if len(line) > 600:
            warnings.append(Finding("warning", "LONG_PARAGRAPH", path.relative_to(root).as_posix(), line_number, "paragraph is too long for quick reading"))
        is_prohibition = any(
            marker in line.lower()
            for marker in (
                "kullanmayın",
                "yazmayın",
                "yazılmaz",
                "kanıtsız pazarlama",
                "kanıtlanmayan",
                "do not use",
                "must not",
            )
        )
        if MARKETING.search(line) and not is_prohibition:
            warnings.append(Finding("warning", "UNPROVEN_SUPERLATIVE", path.relative_to(root).as_posix(), line_number, "review marketing language and require evidence"))
        if PASSIVE_TR.search(line):
            warnings.append(Finding("warning", "PASSIVE_VOICE", path.relative_to(root).as_posix(), line_number, "prefer a direct active sentence"))
        if len(TECHNICAL_DENSITY.findall(line)) >= 4:
            warnings.append(Finding("warning", "TERM_DENSITY", path.relative_to(root).as_posix(), line_number, "explain dense technical terms in plain language"))
    return errors, warnings


def _repository_contract_errors(root: pathlib.Path) -> list[Finding]:
    errors: list[Finding] = []
    canonical = root / "README.md"
    alias = root / "README.en.md"
    if canonical.is_file() and alias.is_file() and canonical.read_bytes() != alias.read_bytes():
        errors.append(Finding("error", "README_ALIAS_DRIFT", "README.en.md", 1, "English README alias differs from canonical README.md"))
    version_file = root / "VERSION"
    if version_file.is_file() and canonical.is_file():
        version = version_file.read_text(encoding="utf-8").strip()
        if f"**Source line:** v{version}" not in canonical.read_text(encoding="utf-8"):
            errors.append(Finding("error", "STALE_VERSION", "README.md", 1, "README source line does not match VERSION"))
    retired = root / "registry" / "retired-public-paths.json"
    if retired.is_file():
        paths = json.loads(retired.read_text(encoding="utf-8"))
        for public in public_files(root):
            text = public.read_text(encoding="utf-8")
            for old_path in paths:
                if old_path in text:
                    errors.append(Finding("error", "RETIRED_REFERENCE", public.relative_to(root).as_posix(), 1, f"reference uses retired path: {old_path}"))
    return errors


def inspect(root: pathlib.Path = ROOT, files: tuple[pathlib.Path, ...] | None = None) -> Report:
    root = root.resolve()
    errors: list[Finding] = []
    warnings: list[Finding] = []
    selected = files if files is not None else public_files(root)
    for path in selected:
        file_errors, file_warnings = _inspect_file(root, path.resolve())
        errors.extend(file_errors)
        warnings.extend(file_warnings)
    selected_names = {path.resolve() for path in selected}
    canonical_pair = {(root / "README.md").resolve(), (root / "README.en.md").resolve()}
    if canonical_pair.issubset(selected_names):
        errors.extend(_repository_contract_errors(root))
    key = lambda finding: (finding.path, finding.line, finding.code, finding.message)
    return Report(tuple(sorted(errors, key=key)), tuple(sorted(warnings, key=key)))


def payload(report: Report) -> dict:
    status = "error" if report.errors else ("warning" if report.warnings else "clean")
    return {
        "status": status,
        "error_count": len(report.errors),
        "warning_count": len(report.warnings),
        "errors": [finding._asdict() for finding in report.errors],
        "warnings": [finding._asdict() for finding in report.warnings],
    }


def to_json(report: Report) -> str:
    return json.dumps(payload(report), ensure_ascii=False, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Divan public writing")
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = inspect()
    if args.json:
        print(to_json(report))
    else:
        for finding in (*report.errors, *report.warnings):
            print(f"{finding.level.upper()} {finding.code} {finding.path}:{finding.line} {finding.message}")
        print(f"PROSE {payload(report)['status'].upper()} - {len(report.errors)} error, {len(report.warnings)} warning")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
