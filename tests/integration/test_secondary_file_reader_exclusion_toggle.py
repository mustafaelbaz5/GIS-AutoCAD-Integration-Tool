"""Test for SecondaryFileReader's apply_exclusion toggle, per project brief §7.3.

Uses a tiny synthetic workbook (not the real sample file) so this runs
fast and independent of whether the real files are present.
"""

from pathlib import Path
from typing import Any

import openpyxl
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper

CONFIG: dict[str, Any] = {
    "sheet_name": "Sheet1",
    "data_starts_at_row": 2,
    "exclude_when": {"column": "M", "values": ["لاغى", "لاغي"]},
    "fields": {
        "رقم_الحيازة": "K",
        "اسم_الحائز": "N",
    },
}


def _write_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(["K header", "M header", "N header"])
    excluded_row = {"K": "1", "M": "لاغى", "N": "Excluded Holder"}
    kept_row = {"K": "2", "M": None, "N": "Kept Holder"}
    for row in (excluded_row, kept_row):
        sheet["K2" if row["K"] == "1" else "K3"] = row["K"]
        sheet["M2" if row["K"] == "1" else "M3"] = row["M"]
        sheet["N2" if row["K"] == "1" else "N3"] = row["N"]
    workbook.save(path)


def test_excludes_laghi_rows_by_default(tmp_path: Path) -> None:
    path = tmp_path / "secondary.xlsx"
    _write_workbook(path)
    mapper = YamlColumnMapper(CONFIG["fields"])

    records = SecondaryFileReader(path, mapper, CONFIG).read()

    holding_ids = {r.holding_id_raw for r in records}
    assert holding_ids == {"2"}


def test_include_laghi_rows_when_apply_exclusion_is_false(tmp_path: Path) -> None:
    path = tmp_path / "secondary.xlsx"
    _write_workbook(path)
    mapper = YamlColumnMapper(CONFIG["fields"])

    records = SecondaryFileReader(path, mapper, CONFIG, apply_exclusion=False).read()

    holding_ids = {r.holding_id_raw for r in records}
    assert holding_ids == {"1", "2"}
