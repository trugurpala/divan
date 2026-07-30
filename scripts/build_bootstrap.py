#!/usr/bin/env python3
"""Build Divan's deterministic, stdlib-only clean-host bootstrap zipapp."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import zipfile
from typing import Any

SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_project_runner
import bootstrap_contract

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOST_FILES = (
    "bootstrap_contract.py",
    "divan.py",
    "host_adapters.py",
    "host_cli.py",
    "host_controller.py",
    "host_install_authority.py",
    "host_install_journal.py",
    "host_journal.py",
    "host_journal_scan.py",
    "host_journal_transitions.py",
    "host_lifecycle.py",
    "host_options.py",
    "host_probe.py",
    "host_profiles.py",
    "host_state.py",
    "host_transactions.py",
    "host_upgrade.py",
    "legacy_state.py",
)
PLATFORM_FILES = (
    "install_codex.ps1",
    "install_codex.sh",
    "uninstall_codex.ps1",
    "uninstall_codex.sh",
)
GENERATED_FILES = (
    "__main__.py",
    "VERSION",
    "divan-bootstrap-catalog.json",
    "divan-bootstrap-source.json",
)
ENTRYPOINT = """\
import pathlib
import runpy
import sys
import tempfile
import zipfile

if __name__ == "__main__":
    bootstrap = pathlib.Path(sys.argv[0]).resolve()
    with tempfile.TemporaryDirectory(prefix="divan-bootstrap-") as directory:
        with zipfile.ZipFile(bootstrap) as archive:
            archive.extractall(directory)
        scripts = pathlib.Path(directory) / "scripts"
        sys.path.insert(0, str(scripts))
        sys._divan_bootstrap_path = str(bootstrap)
        runpy.run_path(str(scripts / "divan.py"), run_name="__main__")
""".encode("utf-8")


def _version(root: pathlib.Path) -> str:
    value = (root / "VERSION").read_text(encoding="utf-8").strip()
    pattern = (
        r"(?:0|[1-9][0-9]*)\."
        r"(?:0|[1-9][0-9]*)\."
        r"(?:0|[1-9][0-9]*)"
    )
    if re.fullmatch(pattern, value) is None:
        raise ValueError("VERSION must contain canonical semantic version text")
    return value


def _catalog(root: pathlib.Path, version: str) -> dict[str, Any]:
    path = root / ".agents" / "plugins" / "marketplace.json"
    try:
        raw = path.read_bytes()
        marketplace = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("cannot read the canonical plugin catalog") from error
    packages: dict[str, dict[str, Any]] = {}
    for plugin in marketplace.get("plugins", []):
        if not isinstance(plugin, dict):
            continue
        name = plugin.get("name")
        package_version = plugin.get("version")
        source = plugin.get("source")
        if (
            not isinstance(name, str)
            or not isinstance(package_version, str)
            or not isinstance(source, dict)
            or not isinstance(source.get("path"), str)
        ):
            continue
        package = root / source["path"]
        skills = sorted(
            skill.parent.name for skill in (package / "skills").glob("*/SKILL.md")
        )
        packages[name] = {"skills": skills, "version": package_version}
    expected = {"sadrazam", "core-pack", "ui-pack", "react-pack", "zanaat-pack"}
    unique_skills = {
        skill for package in packages.values() for skill in package["skills"]
    }
    if set(packages) != expected or len(unique_skills) != 41:
        raise ValueError("plugin catalog must define five packages and 41 unique skills")
    return {
        "marketplace_digest": hashlib.sha256(raw).hexdigest(),
        "packages": packages,
        "schema_version": 1,
        "skill_count": len(unique_skills),
        "version": version,
    }


def _runtime_names(root: pathlib.Path) -> tuple[str, ...]:
    runtime = root / "plugins" / "sadrazam" / "divan_runtime"
    return build_project_runner.runtime_files(runtime)


def archive_names(root: pathlib.Path = ROOT) -> tuple[str, ...]:
    """Return the exact bounded bootstrap inventory."""
    root = root.resolve()
    runtime = (
        f"plugins/sadrazam/divan_runtime/{name}"
        for name in _runtime_names(root)
    )
    data = ("plugins/sadrazam/divan_runtime/data/seo-policy.json",)
    scripts = (f"scripts/{name}" for name in (*HOST_FILES, *PLATFORM_FILES))
    return tuple(sorted({*GENERATED_FILES, *runtime, *data, *scripts}))


def _entries(
    root: pathlib.Path, source_commit: str
) -> dict[str, bytes]:
    version = _version(root)
    catalog = _catalog(root, version)
    runtime = root / "plugins" / "sadrazam" / "divan_runtime"
    entries = {
        f"scripts/{name}": (root / "scripts" / name).read_bytes()
        for name in (*HOST_FILES, *PLATFORM_FILES)
    }
    entries.update(
        {
            f"plugins/sadrazam/divan_runtime/{name}": (runtime / name).read_bytes()
            for name in _runtime_names(root)
        }
    )
    entries["plugins/sadrazam/divan_runtime/data/seo-policy.json"] = (
        root / "registry" / "seo-policy.json"
    ).read_bytes()
    entries["__main__.py"] = ENTRYPOINT
    entries["VERSION"] = f"{version}\n".encode("utf-8")
    entries["divan-bootstrap-catalog.json"] = (
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    identity = {
        "schema_version": 1,
        "source_commit": source_commit,
        "source_ref": f"v{version}",
        "source_repository": "https://github.com/trugurpala/divan.git",
        "version": version,
    }
    bootstrap_contract.validate(identity, catalog)
    entries["divan-bootstrap-source.json"] = (
        json.dumps(identity, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")
    if set(entries) != set(archive_names(root)):
        raise ValueError("bootstrap inventory does not match the bounded catalog")
    return entries


def build(
    output: pathlib.Path,
    source_commit: str,
    root: pathlib.Path = ROOT,
) -> None:
    root = root.resolve()
    build_project_runner._verified_head(root, source_commit)
    entries = _entries(root, source_commit)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=True) as archive:
        for name in sorted(entries):
            build_project_runner._write_entry(archive, name, entries[name])


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
