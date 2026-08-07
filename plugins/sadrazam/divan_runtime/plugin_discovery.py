from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Callable, Iterable

from .executable_locator import locate_executable
from .plugin_contract import ManifestValidation, PluginIssue
from .plugin_manifest_validation import validate_manifest_payload


@dataclass(frozen=True)
class PluginCandidate:
    manifest_path: str
    manifest_sha256: str
    validation: ManifestValidation
    executable_path: str | None
    executable_sha256: str | None

    @property
    def plugin_id(self) -> str | None:
        manifest = self.validation.manifest
        return None if manifest is None else manifest.plugin_id

    @property
    def available(self) -> bool:
        return self.executable_path is not None and self.executable_sha256 is not None


ExecutableLocator = Callable[[str], str | None]


def _default_executable_locator(name: str) -> str | None:
    return locate_executable((name,))


def load_plugin_candidate(
    manifest_path: pathlib.Path | str,
    *,
    executable_locator: ExecutableLocator = _default_executable_locator,
) -> PluginCandidate:
    """Read a static manifest without importing or executing third-party plugin code."""
    path = pathlib.Path(manifest_path)
    if path.is_symlink():
        validation = ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_SYMLINK_REJECTED",
                    "$",
                    "plugin manifests must be regular files, not symlinks",
                ),
            ),
        )
        return PluginCandidate(str(path), "", validation, None, None)

    try:
        raw = path.read_bytes()
    except OSError as error:
        validation = ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_UNREADABLE",
                    "$",
                    f"plugin manifest cannot be read: {error.__class__.__name__}",
                ),
            ),
        )
        return PluginCandidate(str(path), "", validation, None, None)

    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        validation = ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_INVALID_JSON",
                    "$",
                    "plugin manifest must be valid UTF-8 JSON",
                ),
            ),
        )
        return PluginCandidate(str(path), manifest_sha256, validation, None, None)

    validation = validate_manifest_payload(payload)
    manifest = validation.manifest
    if manifest is None:
        return PluginCandidate(str(path), manifest_sha256, validation, None, None)

    executable_path = executable_locator(manifest.executable)
    executable_sha256 = None
    if executable_path is not None:
        executable_sha256 = _sha256_file(pathlib.Path(executable_path))

    return PluginCandidate(
        manifest_path=str(path),
        manifest_sha256=manifest_sha256,
        validation=validation,
        executable_path=executable_path,
        executable_sha256=executable_sha256,
    )


def discover_plugins(
    roots: Iterable[pathlib.Path | str],
    *,
    executable_locator: ExecutableLocator = _default_executable_locator,
) -> tuple[PluginCandidate, ...]:
    """Discover only direct JSON children of explicitly supplied roots."""
    candidates: list[PluginCandidate] = []
    for root_value in roots:
        root = pathlib.Path(root_value)
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            if path.suffix.lower() != ".json":
                continue
            candidates.append(
                load_plugin_candidate(path, executable_locator=executable_locator)
            )
    return tuple(candidates)


def _sha256_file(path: pathlib.Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None
