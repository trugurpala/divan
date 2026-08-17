from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Callable, Iterable

from .executable_locator import locate_executable
from .plugin_contract import ManifestValidation, PluginIssue
from .plugin_manifest_validation import validate_manifest_payload

#: A plugin manifest is a small static declaration. Anything larger is not a
#: manifest, and reading it unbounded lets a crafted file wedge the client.
MAX_MANIFEST_BYTES = 64 * 1024


class _DuplicateKey(ValueError):
    """Raised when a manifest object declares the same key twice."""


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Fail closed on duplicate keys instead of silently keeping the last one.

    The manifest hash attests the bytes. If a duplicate key were accepted,
    the attested bytes would say something the owner never saw on screen.
    """
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen[key] = value
    return seen


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
        size = path.stat().st_size
    except OSError:
        size = None
    if size is not None and size > MAX_MANIFEST_BYTES:
        validation = ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_TOO_LARGE",
                    "$",
                    f"plugin manifest must be at most {MAX_MANIFEST_BYTES} bytes",
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
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except _DuplicateKey as duplicate:
        validation = ManifestValidation(
            None,
            (
                PluginIssue(
                    "PLUGIN_MANIFEST_DUPLICATE_KEY",
                    f"$.{duplicate.args[0]}",
                    "plugin manifest declares the same key twice",
                ),
            ),
        )
        return PluginCandidate(str(path), manifest_sha256, validation, None, None)
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
