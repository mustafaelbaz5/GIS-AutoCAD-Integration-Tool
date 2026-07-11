"""Resolves the application root, both running from source and frozen.

PyInstaller's `--onefile` mode extracts bundled data to a temporary
directory at `sys._MEIPASS`; code that locates bundled resources (the
default column mappings, fonts) must resolve against that when frozen,
and against the project root otherwise.
"""

import sys
from pathlib import Path


def get_app_root() -> Path:
    """Return the project root (source tree) or the frozen bundle root."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass)
    return Path(__file__).resolve().parents[2]
