from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

Which = Callable[[str], str | None]


def locate_executable(
    aliases: Sequence[str],
    *,
    which: Which = shutil.which,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Resolve a local executable without recursively scanning the user's disk.

    PATH remains authoritative. On Windows, Divan also checks a short list of
    standard per-user shim directories used by npm, winget and native CLI
    installers. Values are paths only; no account credentials are inspected.
    """

    for alias in aliases:
        value = which(alias)
        if value:
            return str(Path(value))
    if sys.platform != "win32" or which is not shutil.which:
        return None

    environment = os.environ if env is None else env
    extensions = _windows_extensions(environment)
    for root in _windows_roots(environment):
        for alias in aliases:
            for candidate in _candidates(root, alias, extensions):
                if candidate.is_file():
                    return str(candidate.resolve())
    return None


def _windows_roots(env: Mapping[str, str]) -> tuple[Path, ...]:
    values: list[Path] = []
    appdata = env.get("APPDATA")
    local_appdata = env.get("LOCALAPPDATA")
    userprofile = env.get("USERPROFILE")
    if appdata:
        values.append(Path(appdata) / "npm")
    if local_appdata:
        values.append(Path(local_appdata) / "Microsoft" / "WinGet" / "Links")
    if userprofile:
        values.extend((Path(userprofile) / ".local" / "bin", Path(userprofile) / "bin"))
    return tuple(_dedupe(values))


def _windows_extensions(env: Mapping[str, str]) -> tuple[str, ...]:
    raw = env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    values = [item.strip().lower() for item in raw.split(";") if item.strip()]
    return tuple(dict.fromkeys(("", *values)))


def _candidates(root: Path, alias: str, extensions: Sequence[str]) -> tuple[Path, ...]:
    name = Path(alias).name
    if Path(name).suffix:
        return (root / name,)
    return tuple(root / f"{name}{extension}" for extension in extensions)


def _dedupe(values: Sequence[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for value in values:
        key = str(value).casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
