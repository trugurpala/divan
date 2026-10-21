from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

if __package__:
    from .divan_v2_validate import validate_repository
else:
    from divan_v2_validate import validate_repository

MAX_COMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ENTRIES = 5000
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 100 * 1024 * 1024
MAX_PATH_DEPTH = 20


def _is_publishable_file(relative: Path) -> bool:
    # The alpha ships prose skills, their Markdown references, metadata, and
    # notices. New executable/asset formats need an intentional contract change.
    if relative.as_posix() in {
        ".codex-plugin/plugin.json", "README.md", "LICENSE", "THIRD_PARTY_LICENSES.md",
    }:
        return True
    parts = relative.parts
    if len(parts) == 3 and parts[0] == "skills" and parts[2] in {"SKILL.md", "LICENSE"}:
        return True
    return (
        len(parts) == 4 and parts[0] == "skills" and parts[2] == "references"
        and relative.suffix == ".md" and not relative.name.startswith(".")
    )


def _reject_link(path: Path) -> None:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise ValueError(f"package tree must not contain links: {path}")


def build_package(repo: Path, output: Path) -> dict[str, int]:
    repo = repo.resolve()
    plugin_root = repo / "plugins" / "divan"
    if not plugin_root.is_dir():
        raise FileNotFoundError(f"missing plugin root: {plugin_root}")

    _reject_link(plugin_root.parent)
    _reject_link(plugin_root)
    output = output.resolve()
    if output.is_relative_to(plugin_root):
        raise ValueError("package output must be outside the plugin tree")

    files = []
    for path in sorted(plugin_root.rglob("*")):
        _reject_link(path)
        if path.is_dir():
            continue
        relative = path.relative_to(plugin_root)
        if not path.is_file() or not _is_publishable_file(relative):
            raise ValueError(f"unapproved package file: {relative.as_posix()}")
        files.append(path)

    errors = validate_repository(repo)
    if errors:
        raise ValueError("invalid Divan repository:\n" + "\n".join(errors))

    if len(files) > MAX_ENTRIES:
        raise ValueError(f"package has too many entries: {len(files)} > {MAX_ENTRIES}")

    extracted = 0
    for path in files:
        size = path.stat().st_size
        extracted += size
        if size > MAX_SINGLE_FILE_BYTES:
            raise ValueError(f"package member exceeds {MAX_SINGLE_FILE_BYTES} bytes: {path}")
        rel = path.relative_to(plugin_root)
        if len(rel.parts) > MAX_PATH_DEPTH:
            raise ValueError(f"package path depth exceeds {MAX_PATH_DEPTH}: {rel}")

    if extracted > MAX_EXTRACTED_BYTES:
        raise ValueError(f"package extracted size exceeds {MAX_EXTRACTED_BYTES} bytes")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                rel = path.relative_to(plugin_root).as_posix()
                info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())

        compressed = temporary.stat().st_size
        if compressed > MAX_COMPRESSED_BYTES:
            raise ValueError(f"package compressed size exceeds {MAX_COMPRESSED_BYTES} bytes")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    return {"entries": len(files), "compressed_bytes": compressed, "extracted_bytes": extracted}


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    errors = validate_repository(repo)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    manifest = json.loads((repo / "plugins/divan/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
    output = repo / "dist" / f"divan-{manifest['version']}.zip"
    try:
        report = build_package(repo, output)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Divan package: {output}")
    print(f"entries={report['entries']} compressed={report['compressed_bytes']} extracted={report['extracted_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
