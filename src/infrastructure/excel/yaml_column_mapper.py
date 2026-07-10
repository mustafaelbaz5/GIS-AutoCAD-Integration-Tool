"""Maps a raw secondary-file row to a `ParcelRecord`, via YAML mapping."""

from typing import Any

from src.application.dto.parcel_record import ParcelRecord
from src.application.ports.column_mapper_port import ColumnMapperPort
from src.infrastructure.excel.cell_parsing import clean_text, normalize_national_id, parse_number


class YamlColumnMapper(ColumnMapperPort):
    """Translates a raw row (column letter -> value) using a YAML mapping.

    The "الحوض" field is type-sensitive in the real seasonal-survey
    export: it holds a numeric basin code for most rows but a literal
    basin-name string for others. This mapper inspects the cell's
    Python type to route it to `basin_code` or `basin_name`
    accordingly, since a static column-letter mapping cannot express
    that distinction.
    """

    def __init__(self, fields: dict[str, str]) -> None:
        self._fields = fields

    def map(self, raw_row: dict[str, Any]) -> ParcelRecord:
        """Map a raw row keyed by column letter to a `ParcelRecord`."""

        def cell(field_name: str) -> Any:
            column = self._fields.get(field_name)
            return raw_row.get(column) if column else None

        basin_name, basin_code = self._split_basin(cell("الحوض"))

        return ParcelRecord(
            holding_id_raw=clean_text(cell("رقم_الحيازة")),
            page_number=None,
            directorate=None,
            administration=None,
            basin_name=basin_name,
            basin_code=basin_code,
            holder_name=clean_text(cell("اسم_الحائز")),
            national_id=normalize_national_id(cell("الرقم_القومي")),
            east=None,
            south=None,
            west=None,
            north=None,
            land_number=None,
            feddan=parse_number(cell("فدان")),
            qirat=parse_number(cell("قيراط")),
            sahm=parse_number(cell("سهم")),
        )

    def _split_basin(self, raw_value: Any) -> tuple[str | None, str | None]:
        if isinstance(raw_value, str):
            text = clean_text(raw_value)
            return (text, None) if text is not None else (None, None)
        code = clean_text(raw_value)
        return (None, code)
