"""Reader for the secondary (variable-schema) Excel file."""

from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import column_index_from_string

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

    Uses `read_only=True` and only reads the specific columns the
    mapping declares (rather than every column up to the sheet's
    width), since this file has dozens of unused columns per row.
    """

    def __init__(
        self,
        path: Path,
        mapper: ColumnMapperPort,
        config: dict[str, Any],
        apply_exclusion: bool = True,
    ) -> None:
        self._path = path
        self._mapper = mapper
        self._config = config
        self._apply_exclusion = apply_exclusion

    def read(self) -> list[ParcelRecord]:
        """Read, exclude, and map all data rows to `ParcelRecord`s."""
        workbook = openpyxl.load_workbook(self._path, data_only=True, read_only=True)
        sheet_name = self._config.get("sheet_name")
        worksheet = workbook[sheet_name] if sheet_name else workbook.active

        data_start = int(self._config["data_starts_at_row"])
        exclude_config = self._config.get("exclude_when") if self._apply_exclusion else None
        fields: dict[str, str] = self._config["fields"]

        needed_columns = set(fields.values())
        if exclude_config:
            needed_columns.add(exclude_config["column"])
        column_indices = {col: column_index_from_string(col) for col in needed_columns}
        max_col = max(column_indices.values())

        records: list[ParcelRecord] = []
        for row in worksheet.iter_rows(min_row=data_start, max_col=max_col):
            raw_row = {col: row[index - 1].value for col, index in column_indices.items()}
            if self._is_excluded(raw_row, exclude_config):
                continue
            record = self._mapper.map(raw_row)
            if record.holding_id_raw is None:
                continue
            records.append(record)

        return records

    def _is_excluded(self, raw_row: dict[str, Any], exclude_config: dict[str, Any] | None) -> bool:
        if not exclude_config:
            return False
        value = raw_row.get(exclude_config["column"])
        if value is None:
            return False
        normalized_value = normalize_arabic(str(value))
        excluded_values = {normalize_arabic(v) for v in exclude_config["values"]}
        return normalized_value in excluded_values
