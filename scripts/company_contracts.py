"""Repository-level loader for the installed Company OS contracts."""
from __future__ import annotations

import importlib.util
import pathlib


def validate(root: pathlib.Path) -> list[str]:
    """Return contract loading errors without importing project code."""
    engine_path = root / "plugins" / "sadrazam" / "company" / "engine.py"
    spec = importlib.util.spec_from_file_location("divan_company_validate", engine_path)
    if spec is None or spec.loader is None:
        return ["Company OS engine could not be loaded"]
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        module.load_contracts(engine_path.parent)
    except (OSError, ValueError, TypeError) as exc:
        return [str(exc)]
    return []
