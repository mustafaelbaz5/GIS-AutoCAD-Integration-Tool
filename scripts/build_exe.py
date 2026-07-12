"""Builds a Windows .exe via PyInstaller, per Iteration 4 Task F.

Usage:
    python scripts/build_exe.py

Bundles the default column-mapping YAML files and the entire
`presentation/web/` static-asset tree (HTML/CSS/JS, shared fonts,
icons) that pywebview loads at runtime, plus an icon from
`resources/icons/app.ico` if present.

Requires the Microsoft Edge WebView2 Runtime on the target machine
(ships with Windows 11 and recent Windows 10 updates; see README.md).
"""

import sys
from pathlib import Path

from PyInstaller.__main__ import run as pyinstaller_run

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENTRY_POINT = _PROJECT_ROOT / "src" / "main.py"
_ICON_PATH = _PROJECT_ROOT / "resources" / "icons" / "app.ico"
_DEFAULT_MAPPINGS_DIR = _PROJECT_ROOT / "src" / "infrastructure" / "config" / "default_mappings"
_WEB_ASSETS_DIR = _PROJECT_ROOT / "src" / "presentation" / "web"

_DATA_SEPARATOR = ";" if sys.platform.startswith("win") else ":"


def _add_data_arg(source: Path, dest_relative: str) -> str:
    return f"{source}{_DATA_SEPARATOR}{dest_relative}"


def build_args() -> list[str]:
    """Construct the PyInstaller CLI argument list."""
    if not _WEB_ASSETS_DIR.exists():
        raise FileNotFoundError(
            f"Web assets directory not found: {_WEB_ASSETS_DIR} "
            "(pywebview has nothing to load without it)"
        )

    args = [
        str(_ENTRY_POINT),
        "--name=GIS_AutoCAD_Tool",
        "--onefile",
        "--windowed",
        "--noconfirm",
        f"--distpath={_PROJECT_ROOT / 'dist'}",
        f"--workpath={_PROJECT_ROOT / 'build'}",
        "--add-data",
        _add_data_arg(_DEFAULT_MAPPINGS_DIR, "src/infrastructure/config/default_mappings"),
        "--add-data",
        _add_data_arg(_WEB_ASSETS_DIR, "src/presentation/web"),
    ]

    if _ICON_PATH.exists():
        args.append(f"--icon={_ICON_PATH}")
    else:
        print(
            f"Warning: no icon found at {_ICON_PATH}; building with PyInstaller's default icon.",
            file=sys.stderr,
        )

    return args


def main() -> None:
    pyinstaller_run(build_args())


if __name__ == "__main__":
    main()
