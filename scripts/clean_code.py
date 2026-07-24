#!/usr/bin/env python3
"""Measure first-party Python debt and enforce a shrinking legacy baseline."""

from __future__ import annotations

import argparse
import ast
import io
import json
import pathlib
import re
import subprocess
import sys
import tokenize
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = ROOT / "registry" / "clean-code-baseline.json"
LIMITS = {"module-lines": 400, "function-lines": 50, "complexity": 10}
KINDS = (*LIMITS, "silent-broad-except")
COMPLEXITY_PATTERN = re.compile(r"`(?P<symbol>[^`]+)` is too complex \((?P<value>\d+) > 10\)")


class CleanCodeError(RuntimeError):
    """An actionable clean-code measurement or baseline error."""


class SourceMetrics(ast.NodeVisitor):
    """Collect function length and silent broad-exception findings."""

    def __init__(self, path: str, logical_lines: set[int]) -> None:
        self.path = path
        self.logical_lines = logical_lines
        self.scope: list[str] = []
        self.function_lines: dict[str, int] = {}
        self.silent_broad: dict[str, int] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        target = self._target()
        length = sum(node.lineno <= line <= (node.end_lineno or node.lineno) for line in self.logical_lines)
        if length > LIMITS["function-lines"]:
            self.function_lines[target] = length
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if _is_broad_exception(node.type) and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            target = self._target()
            self.silent_broad[target] = self.silent_broad.get(target, 0) + 1
        self.generic_visit(node)

    def _target(self) -> str:
        symbol = ".".join(self.scope) if self.scope else "<module>"
        return f"{self.path}:{symbol}"


def _is_broad_exception(node: ast.expr | None) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(_is_broad_exception(item) for item in node.elts)
    return False


def _logical_lines(source: str) -> set[int]:
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        return {token.start[0] for token in tokens if token.type == tokenize.NEWLINE}
    except tokenize.TokenError as error:
        raise CleanCodeError(f"Python source cannot be tokenized: {error}") from error


def _python_paths(root: pathlib.Path) -> list[pathlib.Path]:
    roots = (
        root / "scripts",
        root / "evals",
        root / "plugins" / "sadrazam" / "company",
    )
    return sorted(
        path
        for directory in roots
        if directory.exists()
        for path in directory.rglob("*.py")
    )


def _measure_source(root: pathlib.Path, path: pathlib.Path) -> dict[str, dict[str, int]]:
    relative = path.relative_to(root).as_posix()
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
    except (OSError, UnicodeError, SyntaxError) as error:
        raise CleanCodeError(f"{relative}: Python source cannot be measured: {error}") from error
    metrics = SourceMetrics(relative, _logical_lines(source))
    metrics.visit(tree)
    modules = {}
    line_count = len(source.splitlines())
    if line_count > LIMITS["module-lines"]:
        modules[relative] = line_count
    return {
        "module-lines": modules,
        "function-lines": metrics.function_lines,
        "silent-broad-except": metrics.silent_broad,
    }


def _ruff_complexity(root: pathlib.Path) -> dict[str, int]:
    command = [
        "ruff",
        "check",
        "scripts",
        "evals",
        "plugins/sadrazam/company",
        "--select",
        "C901",
        "--config",
        "lint.mccabe.max-complexity=10",
        "--output-format=json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as error:
        raise CleanCodeError(
            "Ruff is required; install development tools with: pip install -r requirements-dev.txt"
        ) from error
    if completed.returncode not in {0, 1}:
        detail = completed.stderr.strip() or "Ruff returned no diagnostic"
        raise CleanCodeError(f"Ruff C901 measurement failed: {detail}")
    try:
        findings = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as error:
        raise CleanCodeError(f"Ruff returned invalid JSON: {error}") from error
    if not isinstance(findings, list):
        raise CleanCodeError("Ruff C901 output must be a JSON list")
    return _parse_complexity(root, findings)


def _parse_complexity(root: pathlib.Path, findings: list[Any]) -> dict[str, int]:
    measured: dict[str, int] = {}
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("code") != "C901":
            continue
        filename = finding.get("filename")
        message = finding.get("message")
        match = COMPLEXITY_PATTERN.fullmatch(message) if isinstance(message, str) else None
        if not isinstance(filename, str) or match is None:
            raise CleanCodeError("Ruff C901 finding has an unexpected JSON contract")
        path = pathlib.Path(filename)
        resolved = path if path.is_absolute() else root / path
        try:
            relative = resolved.resolve().relative_to(root.resolve()).as_posix()
        except ValueError as error:
            raise CleanCodeError(f"Ruff reported a path outside the repository: {filename}") from error
        measured[f"{relative}:{match.group('symbol')}"] = int(match.group("value"))
    return measured


def measure_python(root: pathlib.Path) -> dict[str, dict[str, int]]:
    """Return current violations grouped by kind and exact path or symbol."""
    measured: dict[str, dict[str, int]] = {kind: {} for kind in KINDS}
    for path in _python_paths(root):
        source_metrics = _measure_source(root, path)
        for kind, values in source_metrics.items():
            measured[kind].update(values)
    measured["complexity"] = _ruff_complexity(root)
    return measured


def _baseline_rows(baseline: dict[str, Any]) -> dict[tuple[str, str], int]:
    if baseline.get("schema_version") != 1 or not isinstance(baseline.get("violations"), list):
        raise CleanCodeError("clean-code baseline must use schema_version 1 and violations list")
    rows: dict[tuple[str, str], int] = {}
    for row in baseline["violations"]:
        if not isinstance(row, dict) or set(row) != {"kind", "target", "value"}:
            raise CleanCodeError("clean-code baseline row must contain kind, target, and value")
        kind, target, value = row["kind"], row["target"], row["value"]
        if kind not in KINDS or not isinstance(target, str) or not target:
            raise CleanCodeError("clean-code baseline row has an invalid kind or target")
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise CleanCodeError("clean-code baseline row value must be a positive integer")
        key = (kind, target)
        if key in rows:
            raise CleanCodeError(f"duplicate clean-code baseline row: {kind} {target}")
        rows[key] = value
    return rows


def compare_baseline(measured: dict[str, dict[str, int]], baseline: dict[str, Any]) -> list[str]:
    """Require the baseline to describe every current violation exactly."""
    allowed = _baseline_rows(baseline)
    errors: list[str] = []
    for kind in KINDS:
        for target, value in sorted(measured.get(kind, {}).items()):
            previous = allowed.get((kind, target))
            if previous is None:
                errors.append(f"new {kind} violation: {target} = {value}")
            elif value > previous:
                errors.append(f"increased {kind} violation: {target} = {value} (baseline {previous})")
    for (kind, target), previous in sorted(allowed.items()):
        current = measured.get(kind, {}).get(target)
        if current is None:
            errors.append(f"removed {kind} violation needs baseline refresh: {target} (baseline {previous})")
        elif current < previous:
            errors.append(
                f"shrunk {kind} violation needs baseline refresh: "
                f"{target} = {current} (baseline {previous})"
            )
    return errors


def _read_baseline(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CleanCodeError(f"clean-code baseline cannot be read: {error}") from error
    if not isinstance(data, dict):
        raise CleanCodeError("clean-code baseline root must be an object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Divan clean-code debt ratchet")
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--json", action="store_true", help="emit machine-readable status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        measured = measure_python(ROOT)
        errors = compare_baseline(measured, _read_baseline(BASELINE))
    except CleanCodeError as error:
        if args.json:
            print(json.dumps({"status": "invalid", "errors": [str(error)]}, ensure_ascii=False))
        else:
            print(f"CLEAN CODE HATASI: {error}", file=sys.stderr)
        return 2
    payload = {"status": "valid" if not errors else "invalid", "errors": errors, "measured": measured}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif errors:
        for diagnostic in errors:
            print(f"CLEAN CODE HATASI: {diagnostic}", file=sys.stderr)
    else:
        print("Clean-code debt baseline valid.")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
