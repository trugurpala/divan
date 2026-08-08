from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "desktop_release_guard.py"
SCRIPTS = str(SCRIPT.parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SPEC = importlib.util.spec_from_file_location("desktop_release_guard_readiness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

DesktopReleaseError = MODULE.DesktopReleaseError
require_stable_release = MODULE.require_stable_release


def _ready_report(*, readiness_source_bound: bool = True) -> dict[str, object]:
    return {
        "updater_configured": True,
        "windows_signing_configured": True,
        "production_readiness_evidence": {
            "verified": True,
            "source_bound": readiness_source_bound,
        },
        "updater_e2e_evidence": {
            "verified": True,
            "source_bound": True,
        },
        "acceptance_evidence": {
            "accepted": True,
            "source_bound": True,
        },
    }


class DesktopReleaseReadinessAuthorityTests(unittest.TestCase):
    def test_verified_readiness_authorizes_promotion_guard_without_private_key(self) -> None:
        ready = require_stable_release(_ready_report(), {})

        self.assertEqual(ready["stable_release"], "READY")

    def test_unbound_readiness_cannot_substitute_for_private_key(self) -> None:
        with self.assertRaisesRegex(
            DesktopReleaseError,
            "production readiness does not prove key usability",
        ):
            require_stable_release(
                _ready_report(readiness_source_bound=False),
                {},
            )


if __name__ == "__main__":
    unittest.main()
