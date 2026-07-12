"""Minimal persisted app settings, per Iteration 2 §8.3.

Deliberately stores only the last-used output folder — never search
history or any other personal data.
"""

import json
from pathlib import Path

_SETTINGS_DIR = Path.home() / ".gis_autocad_tool"
_SETTINGS_FILE = _SETTINGS_DIR / "app_settings.json"

DEFAULT_OUTPUT_DIR = Path.home() / "Desktop" / "GIS_Output"


def load_last_output_dir() -> Path | None:
    """Return the last-used output folder, or None if never saved/unreadable."""
    if not _SETTINGS_FILE.exists():
        return None
    try:
        data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    raw_path = data.get("last_output_dir")
    return Path(raw_path) if raw_path else None


def save_last_output_dir(path: Path) -> None:
    """Persist `path` as the last-used output folder."""
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(
        json.dumps({"last_output_dir": str(path)}, ensure_ascii=False), encoding="utf-8"
    )
