"""Integration tests for BaseFileReader against the real sample file."""

from pathlib import Path

from src.infrastructure.config.yaml_mapping_loader import load_mapping
from src.infrastructure.excel.base_file_reader import BaseFileReader

MAPPING_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "infrastructure"
    / "config"
    / "default_mappings"
    / "system_file_default.yaml"
)


def _read_records(base_file_path: Path) -> list:
    config = load_mapping(MAPPING_PATH)
    return BaseFileReader(base_file_path, config).read()


def test_reads_all_2930_data_rows(base_file_path: Path) -> None:
    records = _read_records(base_file_path)
    assert len(records) == 2930


def test_holding_id_preserves_leading_zeros(base_file_path: Path) -> None:
    records = _read_records(base_file_path)
    assert records[0].holding_id_raw == "010"


def test_known_first_row_holder_and_basin(base_file_path: Path) -> None:
    records = _read_records(base_file_path)
    first = records[0]
    assert first.basin_name == "الشيكاره"
    assert first.holder_name == "وليد خطاب الشاذلى الشاذلى"


def test_border_placeholder_cells_are_normalized_to_none(base_file_path: Path) -> None:
    records = _read_records(base_file_path)
    assert all(r.east != "،،" for r in records)
    assert all(r.west != "،،" for r in records)
    assert all(r.south != "،،" for r in records)
    assert all(r.north != "،،" for r in records)


def test_basin_code_column_is_empty_in_base_file(base_file_path: Path) -> None:
    records = _read_records(base_file_path)
    assert all(r.basin_code is None for r in records)
