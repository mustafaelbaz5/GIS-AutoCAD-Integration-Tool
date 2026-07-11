"""Maps a raw file row to a `ParcelRecord`, via a YAML column mapping.

Handles every declared field generically — no field is hardcoded to a
particular source, since after Iteration 3's reader consolidation
every input file (whatever role it plays) is read through the same
mapping mechanism. A field simply resolves to `None` when the mapping
doesn't declare it, which is what happens automatically for any
mapping that doesn't need a given field (e.g. the real seasonal-survey
export never declares borders/page-number/land-number, so those stay
`None` exactly as before this generalization).
"""

from collections.abc import Callable
from typing import Any

from src.application.dto.parcel_record import ParcelRecord
from src.application.ports.column_mapper_port import ColumnMapperPort
from src.infrastructure.excel.cell_parsing import (
    clean_border,
    clean_text,
    normalize_national_id,
    parse_number,
)

_BASIN_NAME_FIELD = "اسم_الحوض"
_BASIN_CODE_FIELD = "كود_الحوض"
_BASIN_TYPE_SENSITIVE_FIELD = "الحوض"


class YamlColumnMapper(ColumnMapperPort):
    """Translates a raw row (column letter -> value) using a YAML mapping.

    `holding_id_raw` is always left `None` here — join-key extraction
    is `MappedFileReader`'s responsibility, driven by the mapping's
    `join_key_column`, independent of any semantically-named field.
    """

    def __init__(self, fields: dict[str, str]) -> None:
        self._fields = fields

    def map(self, raw_row: dict[str, Any]) -> ParcelRecord:
        """Map a raw row keyed by column letter to a `ParcelRecord`."""

        def cell(field_name: str) -> Any:
            column = self._fields.get(field_name)
            return raw_row.get(column) if column else None

        basin_name, basin_code = self._resolve_basin(cell)

        return ParcelRecord(
            holding_id_raw=None,
            page_number=clean_text(cell("رقم_الصفحة_بالسجل")),
            directorate=clean_text(cell("المديريه")),
            administration=clean_text(cell("الأداره")),
            basin_name=basin_name,
            basin_code=basin_code,
            holder_name=clean_text(cell("اسم_الحائز")),
            national_id=normalize_national_id(cell("الرقم_القومي")),
            east=clean_border(cell("الحد_الشرقى")),
            south=clean_border(cell("الحد_القبلى")),
            west=clean_border(cell("الحد_الغربى")),
            north=clean_border(cell("الحد_البحرى")),
            land_number=clean_text(cell("رقم_الأرض")),
            feddan=parse_number(cell("فدان")),
            qirat=parse_number(cell("قيراط")),
            sahm=parse_number(cell("سهم")),
        )

    def _resolve_basin(self, cell: Callable[[str], Any]) -> tuple[str | None, str | None]:
        """Resolve basin name/code, supporting two mapping styles.

        Some mappings (e.g. the system file) declare separate
        اسم_الحوض/كود_الحوض fields. Others (e.g. the real seasonal
        survey export) declare a single type-sensitive الحوض field
        that holds a numeric code for most rows but a literal name for
        others — inspecting the cell's Python type routes it
        accordingly, since a static column mapping alone can't express
        that distinction.
        """
        has_name_field = _BASIN_NAME_FIELD in self._fields
        has_code_field = _BASIN_CODE_FIELD in self._fields
        if has_name_field or has_code_field:
            name = clean_text(cell(_BASIN_NAME_FIELD)) if has_name_field else None
            code = clean_text(cell(_BASIN_CODE_FIELD)) if has_code_field else None
            return name, code

        if _BASIN_TYPE_SENSITIVE_FIELD in self._fields:
            return self._split_type_sensitive_basin(cell(_BASIN_TYPE_SENSITIVE_FIELD))

        return None, None

    def _split_type_sensitive_basin(self, raw_value: Any) -> tuple[str | None, str | None]:
        if isinstance(raw_value, str):
            text = clean_text(raw_value)
            return (text, None) if text is not None else (None, None)
        code = clean_text(raw_value)
        return (None, code)
