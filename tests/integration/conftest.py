"""Shared fixtures for infrastructure integration tests.

The real sample files live at the project root and are gitignored, so
tests referencing them skip gracefully (rather than fail) when the
files are not present locally.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_FILE_PATH = PROJECT_ROOT / "الاخوه.xlsx"
SECONDARY_FILE_PATH = PROJECT_ROOT / "حصر الصيفي2026 جديد  اول.xlsx"


def _skip_if_missing(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"Real sample file not present: {path.name}")


@pytest.fixture
def base_file_path() -> Path:
    _skip_if_missing(BASE_FILE_PATH)
    return BASE_FILE_PATH


@pytest.fixture
def secondary_file_path() -> Path:
    _skip_if_missing(SECONDARY_FILE_PATH)
    return SECONDARY_FILE_PATH


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    """A single QApplication instance shared across GUI-touching tests."""
    app = QApplication.instance() or QApplication([])
    yield app
