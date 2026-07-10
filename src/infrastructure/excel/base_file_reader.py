"""Reader for the base (system) Excel file — fixed schema."""

from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import column_index_from_string

from src.application.dto.parcel_record import ParcelRecord
from src.application.ports.data_source_port import DataSourcePort
from src.infrastructure.excel.cell_parsing import clean_border, clean_text, parse_number


class BaseFileReader(DataSourcePort):
    """Reads the base (system) file, e.g. الاخوه.xlsx.

    Column letters come from a YAML mapping (see
    `infrastructure/config/default_mappings/system_file_default.yaml`)
    rather than being hard-coded, even though this file's schema is
    fixed, for consistency with the secondary reader and easy
    re-verification if the export format ever shifts.

    Uses `read_only=True` and sequential row iteration: this file's
    thousands of merged cosmetic cells make openpyxl's normal (fully
    parsed) load mode extremely slow — read-only mode avoids building
    that in-memory model and cuts load time from ~20s to under 1s.
    """

    def __init__(self, path: Path, config: dict[str, Any]) -> None:
        self._path = path
        self._config = config

    def read(self) -> list[ParcelRecord]:
        """Read all parcel rows until the holding-ID column goes blank."""
        workbook = openpyxl.load_workbook(self._path, data_only=True, read_only=True)
        sheet_name = self._config.get("sheet_name")
        worksheet = workbook[sheet_name] if sheet_name else workbook.active

        fields: dict[str, str] = self._config["fields"]
        column_indices = {name: column_index_from_string(col) for name, col in fields.items()}
        holding_id_index = column_indices["رقم_الحيازة"]
        max_col = max(column_indices.values())
        data_start = int(self._config["data_starts_at_row"])

        records: list[ParcelRecord] = []
        for row in worksheet.iter_rows(min_row=data_start, max_col=max_col):
            holding_id = clean_text(row[holding_id_index - 1].value)
            if holding_id is None:
                break
            records.append(self._build_record(row, column_indices, holding_id))

        return records

    def _build_record(
        self,
        row: tuple[Any, ...],
        column_indices: dict[str, int],
        holding_id: str,
    ) -> ParcelRecord:
        def cell(field_name: str) -> Any:
            index = column_indices.get(field_name)
            return row[index - 1].value if index else None

        return ParcelRecord(
            holding_id_raw=holding_id,
            page_number=clean_text(cell("رقم_الصفحة_بالسجل")),
            directorate=clean_text(cell("المديريه")),
            administration=clean_text(cell("الأداره")),
            basin_name=clean_text(cell("اسم_الحوض")),
            basin_code=clean_text(cell("كود_الحوض")),
            holder_name=clean_text(cell("اسم_الحائز")),
            national_id=None,
            east=clean_border(cell("الحد_الشرقى")),
            south=clean_border(cell("الحد_القبلى")),
            west=clean_border(cell("الحد_الغربى")),
            north=clean_border(cell("الحد_البحرى")),
            land_number=clean_text(cell("رقم_الأرض")),
            feddan=parse_number(cell("فدان")),
            qirat=parse_number(cell("قيراط")),
            sahm=parse_number(cell("سهم")),
        )
