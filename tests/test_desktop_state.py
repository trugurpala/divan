from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime.desktop_state import WINDOWS_DATA_DIRECTORY, desktop_data_root


class DesktopStateTests(unittest.TestCase):
    def test_explicit_data_override_remains_authoritative(self) -> None:
        with patch.dict(os.environ, {"DIVAN_DATA_DIR": "C:/divan-test-state"}, clear=False):
            self.assertEqual(desktop_data_root(), pathlib.Path("C:/divan-test-state"))

    def test_windows_local_appdata_state_is_identifier_scoped_not_installer_named(self) -> None:
        with patch.dict(
            os.environ,
            {"LOCALAPPDATA": "C:/Users/Test/AppData/Local"},
            clear=False,
        ):
            os.environ.pop("DIVAN_DATA_DIR", None)
            root = desktop_data_root()

        self.assertEqual(
            root,
            pathlib.Path("C:/Users/Test/AppData/Local") / WINDOWS_DATA_DIRECTORY,
        )
        self.assertNotEqual(root.name.casefold(), "divan")


if __name__ == "__main__":
    unittest.main()
