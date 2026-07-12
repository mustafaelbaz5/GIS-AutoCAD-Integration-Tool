"""Tests for yaml_mapping_loader.py's load_mapping and list_available_mappings."""

from pathlib import Path

import pytest
from src.infrastructure.config.yaml_mapping_loader import (
    MappingConfigError,
    list_available_mappings,
    load_mapping,
)


def _write_mapping(
    path: Path, name: str = "Test Mapping", description: str = "A test mapping."
) -> None:
    path.write_text(
        f"""
name: "{name}"
description: "{description}"
sheet_name: "Sheet1"
data_starts_at_row: 2
join_key_column: "A"
fields:
  اسم_الحائز: "B"
""",
        encoding="utf-8",
    )


def test_load_mapping_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(MappingConfigError):
        load_mapping(tmp_path / "missing.yaml")


def test_load_mapping_reads_a_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "valid.yaml"
    _write_mapping(path)

    data = load_mapping(path)

    assert data["fields"] == {"اسم_الحائز": "B"}
    assert data["data_starts_at_row"] == 2


def test_list_available_mappings_returns_one_entry_per_yaml_file(tmp_path: Path) -> None:
    _write_mapping(tmp_path / "a.yaml", name="Mapping A", description="First")
    _write_mapping(tmp_path / "b.yaml", name="Mapping B", description="Second")

    mappings = list_available_mappings(tmp_path)

    assert [m.name for m in mappings] == ["Mapping A", "Mapping B"]
    assert [m.description for m in mappings] == ["First", "Second"]


def test_list_available_mappings_falls_back_to_stem_when_name_missing(tmp_path: Path) -> None:
    path = tmp_path / "no_name.yaml"
    path.write_text(
        "sheet_name: 'Sheet1'\ndata_starts_at_row: 2\njoin_key_column: 'A'\nfields: {}\n",
        encoding="utf-8",
    )

    mappings = list_available_mappings(tmp_path)

    assert mappings[0].name == "no_name"
    assert mappings[0].description == ""


def test_list_available_mappings_skips_non_mapping_yaml_files(tmp_path: Path) -> None:
    (tmp_path / "not_a_mapping.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    _write_mapping(tmp_path / "valid.yaml")

    mappings = list_available_mappings(tmp_path)

    assert len(mappings) == 1
    assert mappings[0].path.name == "valid.yaml"


def test_list_available_mappings_returns_empty_list_for_empty_directory(tmp_path: Path) -> None:
    assert list_available_mappings(tmp_path) == []
