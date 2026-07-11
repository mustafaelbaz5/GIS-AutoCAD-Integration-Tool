"""Builds a Windows .exe via PyInstaller, per project brief Phase 10.

Usage:
    python scripts/build_exe.py

Bundles the default column-mapping YAML files and any font files
present in `resources/fonts/`, and applies an icon from
`resources/icons/app.ico` if present. Excludes unused, heavy Qt
submodules to keep the bundle size down — PySide6 is inherently larger
than the brief's original CustomTkinter-based size target, since RTL
support required switching frameworks (see project history).
"""

import sys
from pathlib import Path

from PyInstaller.__main__ import run as pyinstaller_run

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENTRY_POINT = _PROJECT_ROOT / "src" / "main.py"
_ICON_PATH = _PROJECT_ROOT / "resources" / "icons" / "app.ico"
_DEFAULT_MAPPINGS_DIR = _PROJECT_ROOT / "src" / "infrastructure" / "config" / "default_mappings"
_FONTS_DIR = _PROJECT_ROOT / "resources" / "fonts"

_DATA_SEPARATOR = ";" if sys.platform.startswith("win") else ":"

# Qt submodules this app never uses; excluding them shrinks the bundle
# noticeably since PyInstaller otherwise pulls in all of PySide6.
_EXCLUDED_QT_MODULES = (
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
)


def _add_data_arg(source: Path, dest_relative: str) -> str:
    return f"{source}{_DATA_SEPARATOR}{dest_relative}"


def build_args() -> list[str]:
    """Construct the PyInstaller CLI argument list."""
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
    ]

    has_bundled_fonts = any(_FONTS_DIR.glob("*.ttf")) or any(_FONTS_DIR.glob("*.otf"))
    if has_bundled_fonts:
        args += ["--add-data", _add_data_arg(_FONTS_DIR, "resources/fonts")]
    else:
        print(
            f"Warning: no .ttf/.otf files in {_FONTS_DIR}; "
            "building without a bundled Arabic font (falls back to a system font).",
            file=sys.stderr,
        )

    if _ICON_PATH.exists():
        args.append(f"--icon={_ICON_PATH}")
    else:
        print(
            f"Warning: no icon found at {_ICON_PATH}; building with PyInstaller's default icon.",
            file=sys.stderr,
        )

    for module in _EXCLUDED_QT_MODULES:
        args += ["--exclude-module", module]

    return args


def main() -> None:
    pyinstaller_run(build_args())


if __name__ == "__main__":
    main()
