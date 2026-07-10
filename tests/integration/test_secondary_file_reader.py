"""Integration tests for SecondaryFileReader against the real sample file.

The real file contains duplicate رقم حيازه 2022 values across different
village sections (the same holding number/holder name can appear on
more than one physical row, one excluded and one not) — exclusion is a
per-row rule, not a per-person one. Tests derive their expected values
directly from the raw workbook at run time (via openpyxl), skipping
excluded rows when picking a sample, and assert with `any(...)` to
tolerate legitimate duplicates.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import openpyxl
from src.application.dto.parcel_record import ParcelRecord
from src.infrastructure.config.yaml_mapping_loader import load_mapping
from src.infrastructure.excel.cell_parsing import clean_text, normalize_national_id
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper
from src.shared.arabic_normalizer import normalize_arabic

MAPPING_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "infrastructure"
    / "config"
    / "default_mappings"
    / "seasonal_survey_default.yaml"
)
SHEET_NAME = "سجل 2 خدمات"
DATA_START_ROW = 7
_EXCLUDED_TARGETS = {normalize_arabic("لاغى"), normalize_arabic("لاغي")}


def _read_records(secondary_file_path: Path) -> list[ParcelRecord]:
    config = load_mapping(MAPPING_PATH)
    mapper = YamlColumnMapper(config["fields"])
    return SecondaryFileReader(secondary_file_path, mapper, config).read()


def _raw_rows(secondary_file_path: Path) -> Iterator[dict[str, Any]]:
    workbook = openpyxl.load_workbook(secondary_file_path, data_only=True)
    worksheet = workbook[SHEET_NAME]
    for row_number in range(DATA_START_ROW, worksheet.max_row + 1):
        yield {
            col: worksheet[f"{col}{row_number}"].value
            for col in ("K", "M", "N", "AA", "AB", "AC", "AD", "AF")
        }


def _is_excluded_row(cells: dict[str, Any]) -> bool:
    m_value = cells["M"]
    return m_value is not None and normalize_arabic(str(m_value)) in _EXCLUDED_TARGETS


def test_excludes_laghi_rows(secondary_file_path: Path) -> None:
    excluded_pairs: set[tuple[str, str | None]] = set()
    kept_pairs: set[tuple[str, str | None]] = set()

    for cells in _raw_rows(secondary_file_path):
        holding_id = clean_text(cells["K"])
        if holding_id is None:
            continue
        pair = (holding_id, clean_text(cells["N"]))
        (excluded_pairs if _is_excluded_row(cells) else kept_pairs).add(pair)

    # A pair only belongs in the never-appears set if every row bearing it
    # was excluded — the same (id, name) can legitimately reappear on a
    # separate, non-excluded row elsewhere in the file.
    purely_excluded_pairs = excluded_pairs - kept_pairs
    assert purely_excluded_pairs, "sanity check: expected a لاغى row with no non-excluded duplicate"

    records = _read_records(secondary_file_path)
    present_pairs = {(r.holding_id_raw, r.holder_name) for r in records}
    assert purely_excluded_pairs.isdisjoint(present_pairs)


def test_reads_valid_national_id_matching_source(secondary_file_path: Path) -> None:
    expected = None
    for cells in _raw_rows(secondary_file_path):
        if _is_excluded_row(cells):
            continue
        if cells["AD"] is not None and cells["K"] is not None:
            expected = (clean_text(cells["K"]), normalize_national_id(cells["AD"]))
            break
    assert expected is not None, "sanity check: expected a non-excluded row with a national ID"

    records = _read_records(secondary_file_path)
    assert any(
        (r.holding_id_raw, r.national_id) == expected and len(r.national_id or "") == 14
        for r in records
    )


def test_basin_column_numeric_value_maps_to_basin_code(secondary_file_path: Path) -> None:
    expected = None
    for cells in _raw_rows(secondary_file_path):
        if _is_excluded_row(cells):
            continue
        af = cells["AF"]
        if isinstance(af, int | float) and cells["K"] is not None:
            expected = (clean_text(cells["K"]), clean_text(af))
            break
    assert expected is not None, "sanity check: expected a non-excluded row with a numeric الجوض"

    records = _read_records(secondary_file_path)
    assert any(
        r.holding_id_raw == expected[0] and r.basin_code == expected[1] and r.basin_name is None
        for r in records
    )


def test_basin_column_text_value_maps_to_basin_name(secondary_file_path: Path) -> None:
    expected = None
    for cells in _raw_rows(secondary_file_path):
        if _is_excluded_row(cells):
            continue
        af = cells["AF"]
        if isinstance(af, str) and clean_text(af) is not None and cells["K"] is not None:
            expected = (clean_text(cells["K"]), clean_text(af))
            break
    assert expected is not None, "sanity check: expected a non-excluded row with a text الجوض"

    records = _read_records(secondary_file_path)
    assert any(
        r.holding_id_raw == expected[0] and r.basin_name == expected[1] and r.basin_code is None
        for r in records
    )


def test_area_uses_total_group_not_cultivated_group(secondary_file_path: Path) -> None:
    expected = None
    for cells in _raw_rows(secondary_file_path):
        if _is_excluded_row(cells):
            continue
        if cells["AA"] is not None and cells["K"] is not None:
            expected = (clean_text(cells["K"]), cells["AA"], cells["AB"], cells["AC"])
            break
    assert expected is not None, "sanity check: expected a non-excluded row with جملة area values"

    holding_id, sahm, qirat, feddan = expected
    records = _read_records(secondary_file_path)
    assert any(
        r.holding_id_raw == holding_id
        and r.sahm == sahm
        and r.qirat == qirat
        and r.feddan == feddan
        for r in records
    )
