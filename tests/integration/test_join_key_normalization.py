"""Integration test: join-key normalization (§5.2) across real readers.

Uses small synthetic workbooks (not the real sample files) so this test
always runs, independent of whether the real files are present.
"""

from pathlib import Path
from typing import Any

import openpyxl
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.infrastructure.excel.mapped_file_reader import MappedFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper

PRIMARY_CONFIG: dict[str, Any] = {
    "sheet_name": "Sheet1",
    "data_starts_at_row": 2,
    "join_key_column": "A",
    "fields": {
        "اسم_الحائز": "B",
    },
}

SUPPLEMENTARY_CONFIG: dict[str, Any] = {
    "sheet_name": "Sheet1",
    "data_starts_at_row": 2,
    "join_key_column": "A",
    "fields": {
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
    primary_path = tmp_path / "primary.xlsx"
    supplementary_path = tmp_path / "supplementary.xlsx"

    _write_workbook(primary_path, ["holding_id", "holder"], [["010", "Primary Holder"]])
    _write_workbook(supplementary_path, ["holding_id", "national_id"], [["10", "12345678901234"]])

    primary_mapper = YamlColumnMapper(PRIMARY_CONFIG["fields"])
    primary_reader = MappedFileReader(primary_path, primary_mapper, PRIMARY_CONFIG)
    supplementary_mapper = YamlColumnMapper(SUPPLEMENTARY_CONFIG["fields"])
    supplementary_reader = MappedFileReader(
        supplementary_path, supplementary_mapper, SUPPLEMENTARY_CONFIG
    )

    result = MergeParcelsUseCase(primary_reader, supplementary_reader).execute()

    assert len(result.parcels) == 1
    assert str(result.parcels[0].holding_id) == "010"
    assert result.parcels[0].holder.national_id == "12345678901234"


def test_join_key_does_not_match_unrelated_holding_ids(tmp_path: Path) -> None:
    primary_path = tmp_path / "primary.xlsx"
    supplementary_path = tmp_path / "supplementary.xlsx"

    _write_workbook(primary_path, ["holding_id", "holder"], [["5", "Primary Holder"]])
    _write_workbook(supplementary_path, ["holding_id", "national_id"], [["50", "99999999999999"]])

    primary_mapper = YamlColumnMapper(PRIMARY_CONFIG["fields"])
    primary_reader = MappedFileReader(primary_path, primary_mapper, PRIMARY_CONFIG)
    supplementary_mapper = YamlColumnMapper(SUPPLEMENTARY_CONFIG["fields"])
    supplementary_reader = MappedFileReader(
        supplementary_path, supplementary_mapper, SUPPLEMENTARY_CONFIG
    )

    result = MergeParcelsUseCase(primary_reader, supplementary_reader).execute()

    assert len(result.parcels) == 1
    assert result.parcels[0].holder.national_id is None
