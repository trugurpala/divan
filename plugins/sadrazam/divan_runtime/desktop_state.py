from __future__ import annotations

import os
from pathlib import Path

WINDOWS_DATA_DIRECTORY = "com.ugurpala.ottoman"


def desktop_data_root() -> Path:
    # OTTOMAN_DATA_DIR is the supported escape hatch for portable/test runs.
    # Keep the former variable only as a migration bridge so an existing local
    # automation setup does not silently lose its state during the rename.
    override = os.environ.get("OTTOMAN_DATA_DIR") or os.environ.get("DIVAN_DATA_DIR")
    if override:
        return Path(override).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        # Tauri current-user NSIS installs under LOCALAPPDATA. Keep persistent
        # Core state in an identifier-scoped sibling directory so uninstalling
        # the application cannot remove projects/tasks/evidence by deleting the
        # product installation directory.
        return Path(local_app_data) / WINDOWS_DATA_DIRECTORY
    return Path.home() / ".ottoman"


def task_root() -> Path:
    return desktop_data_root() / "tasks"


def evidence_root() -> Path:
    return desktop_data_root() / "evidence"


def worktree_root() -> Path:
    return desktop_data_root() / "worktrees"


def projects_file() -> Path:
    return desktop_data_root() / "projects.json"
