"""Reader for the secondary (variable-schema) Excel file."""

from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from src.application.dto.parcel_record import ParcelRecord
from src.application.ports.column_mapper_port import ColumnMapperPort
from src.application.ports.data_source_port import DataSourcePort
from src.shared.arabic_normalizer import normalize_arabic


class SecondaryFileReader(DataSourcePort):
    """Reads the secondary (variable-schema) file via a YAML mapping.

    Column letters are never hard-coded here — they come from the
    mapping config, translated to `ParcelRecord`s by the injected
    `ColumnMapperPort`. Applies the exclusion rule (§5.3) after Arabic
    normalization before handing rows to the mapper.
    """

    def __init__(self, path: Path, mapper: ColumnMapperPort, config: dict[str, Any]) -> None:
        self._path = path
        self._mapper = mapper
        self._config = config

    def read(self) -> list[ParcelRecord]:
        """Read, exclude, and map all data rows to `ParcelRecord`s."""
        workbook = openpyxl.load_workbook(self._path, data_only=True)
        sheet_name = self._config.get("sheet_name")
        worksheet: Worksheet = workbook[sheet_name] if sheet_name else workbook.active

        data_start = int(self._config["data_starts_at_row"])
        exclude_config = self._config.get("exclude_when")

        records: list[ParcelRecord] = []
        for row in worksheet.iter_rows(min_row=data_start):
            raw_row = self._row_to_dict(row)
            if self._is_excluded(raw_row, exclude_config):
                continue
            record = self._mapper.map(raw_row)
            if record.holding_id_raw is None:
                continue
            records.append(record)

        return records

    def _row_to_dict(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {get_column_letter(cell.column): cell.value for cell in row}

    def _is_excluded(self, raw_row: dict[str, Any], exclude_config: dict[str, Any] | None) -> bool:
        if not exclude_config:
            return False
        value = raw_row.get(exclude_config["column"])
        if value is None:
            return False
        normalized_value = normalize_arabic(str(value))
        excluded_values = {normalize_arabic(v) for v in exclude_config["values"]}
        return normalized_value in excluded_values
