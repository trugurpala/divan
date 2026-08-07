from __future__ import annotations

import os
from pathlib import Path


def desktop_data_root() -> Path:
    override = os.environ.get("DIVAN_DATA_DIR")
    if override:
        return Path(override).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Divan"
    return Path.home() / ".divan"


def task_root() -> Path:
    return desktop_data_root() / "tasks"


def evidence_root() -> Path:
    return desktop_data_root() / "evidence"
