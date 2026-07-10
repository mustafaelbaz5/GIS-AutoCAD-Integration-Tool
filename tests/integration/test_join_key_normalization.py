"""Integration test: join-key normalization (§5.2) across real readers.

Uses small synthetic workbooks (not the real sample files) so this test
always runs, independent of whether the real files are present.
"""

from pathlib import Path
from typing import Any

import openpyxl
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.infrastructure.excel.base_file_reader import BaseFileReader
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper

BASE_CONFIG: dict[str, Any] = {
    "sheet_name": "Sheet1",
    "data_starts_at_row": 2,
    "fields": {
        "رقم_الحيازة": "A",
        "اسم_الحائز": "B",
    },
}

SECONDARY_CONFIG: dict[str, Any] = {
    "sheet_name": "Sheet1",
    "data_starts_at_row": 2,
    "fields": {
        "رقم_الحيازة": "A",
        "الرقم_القومي": "B",
    },
}


def _write_workbook(path: Path, header: list[str], rows: list[list[object]]) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_join_key_normalizes_leading_zeros_across_files(tmp_path: Path) -> None:
    base_path = tmp_path / "base.xlsx"
    secondary_path = tmp_path / "secondary.xlsx"

    _write_workbook(base_path, ["holding_id", "holder"], [["010", "Base Holder"]])
    _write_workbook(secondary_path, ["holding_id", "national_id"], [["10", "12345678901234"]])

    base_reader = BaseFileReader(base_path, BASE_CONFIG)
    secondary_mapper = YamlColumnMapper(SECONDARY_CONFIG["fields"])
    secondary_reader = SecondaryFileReader(secondary_path, secondary_mapper, SECONDARY_CONFIG)

    result = MergeParcelsUseCase(base_reader, secondary_reader).execute()

    assert len(result.parcels) == 1
    assert str(result.parcels[0].holding_id) == "010"
    assert result.parcels[0].holder.national_id == "12345678901234"


def test_join_key_does_not_match_unrelated_holding_ids(tmp_path: Path) -> None:
    base_path = tmp_path / "base.xlsx"
    secondary_path = tmp_path / "secondary.xlsx"

    _write_workbook(base_path, ["holding_id", "holder"], [["5", "Base Holder"]])
    _write_workbook(secondary_path, ["holding_id", "national_id"], [["50", "99999999999999"]])

    base_reader = BaseFileReader(base_path, BASE_CONFIG)
    secondary_mapper = YamlColumnMapper(SECONDARY_CONFIG["fields"])
    secondary_reader = SecondaryFileReader(secondary_path, secondary_mapper, SECONDARY_CONFIG)

    result = MergeParcelsUseCase(base_reader, secondary_reader).execute()

    assert len(result.parcels) == 1
    assert result.parcels[0].holder.national_id is None
