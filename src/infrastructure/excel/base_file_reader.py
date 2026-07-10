"""Reader for the base (system) Excel file — fixed schema."""

from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

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
    """

    def __init__(self, path: Path, config: dict[str, Any]) -> None:
        self._path = path
        self._config = config

    def read(self) -> list[ParcelRecord]:
        """Read all parcel rows until the holding-ID column goes blank."""
        workbook = openpyxl.load_workbook(self._path, data_only=True)
        sheet_name = self._config.get("sheet_name")
        worksheet: Worksheet = workbook[sheet_name] if sheet_name else workbook.active

        fields: dict[str, str] = self._config["fields"]
        holding_id_column = fields["رقم_الحيازة"]
        row_number = int(self._config["data_starts_at_row"])

        records: list[ParcelRecord] = []
        while True:
            holding_id = clean_text(worksheet[f"{holding_id_column}{row_number}"].value)
            if holding_id is None:
                break
            records.append(self._build_record(worksheet, row_number, fields, holding_id))
            row_number += 1

        return records

    def _build_record(
        self,
        worksheet: Worksheet,
        row_number: int,
        fields: dict[str, str],
        holding_id: str,
    ) -> ParcelRecord:
        def cell(field_name: str) -> Any:
            column = fields.get(field_name)
            return worksheet[f"{column}{row_number}"].value if column else None

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
