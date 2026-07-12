"""Shared fixtures for infrastructure integration tests.

The real sample files live at the project root and are gitignored, so
tests referencing them skip gracefully (rather than fail) when the
files are not present locally.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# The base/system-file sample: parcel-level report with border/basin
# data, matches system_file_default.yaml.
BASE_FILE_PATH = PROJECT_ROOT / "مسجل_م الأخوة.xlsx"

# The external/secondary-file sample: holding-level "approved
# holdings" report, no border data, matches external_file_default.yaml.
SECONDARY_FILE_PATH = PROJECT_ROOT / "م الاخوة.xlsx"

# The older seasonal-survey secondary-file sample (matches
# seasonal_survey_default.yaml). Kept as a separate fixture so its
# tests degrade to a clean skip if this file isn't present locally.
SEASONAL_SECONDARY_FILE_PATH = PROJECT_ROOT / "حصر الصيفي2026 جديد  اول.xlsx"


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


@pytest.fixture
def seasonal_secondary_file_path() -> Path:
    _skip_if_missing(SEASONAL_SECONDARY_FILE_PATH)
    return SEASONAL_SECONDARY_FILE_PATH
