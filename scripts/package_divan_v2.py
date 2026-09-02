from __future__ import annotations

import zipfile
from pathlib import Path

MAX_COMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ENTRIES = 5000
MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 100 * 1024 * 1024
MAX_PATH_DEPTH = 20


def build_package(repo: Path, output: Path) -> dict[str, int]:
    repo = repo.resolve()
    plugin_root = repo / "plugins" / "divan"
    if not plugin_root.is_dir():
        raise FileNotFoundError(f"missing plugin root: {plugin_root}")

    files = sorted(path for path in plugin_root.rglob("*") if path.is_file())
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
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(plugin_root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    compressed = output.stat().st_size
    if compressed > MAX_COMPRESSED_BYTES:
        output.unlink(missing_ok=True)
        raise ValueError(f"package compressed size exceeds {MAX_COMPRESSED_BYTES} bytes")

    return {"entries": len(files), "compressed_bytes": compressed, "extracted_bytes": extracted}


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    output = repo / "dist" / "divan-2.0.0-alpha.1.zip"
    report = build_package(repo, output)
    print(f"Divan package: {output}")
    print(f"entries={report['entries']} compressed={report['compressed_bytes']} extracted={report['extracted_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
