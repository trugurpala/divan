"""Compatibility alias for :mod:`divan_runtime.receipts`."""
import pathlib
import sys

DIRECTORY = pathlib.Path(__file__).resolve().parent
if str(DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DIRECTORY))
from _compat import expose  # noqa: E402

expose("receipts", globals())
