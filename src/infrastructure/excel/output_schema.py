"""The final output's 17-column schema, per project brief §6.2.

Single source of truth for the Arabic column headers and how each is
derived from a `Parcel`, so header text is never scattered as magic
strings across the writer.
"""

from collections.abc import Callable
from dataclasses import dataclass

from src.domain.entities.parcel import Parcel
from src.domain.services.area_calculator import AreaCalculator


@dataclass(frozen=True)
class OutputColumn:
    """One column of the final output file."""

    header: str
    getter: Callable[[Parcel], object]
    is_numeric: bool = False
    is_text_national_id: bool = False


def _total_sqm(parcel: Parcel) -> float | None:
    return AreaCalculator.calculate_total_sqm(parcel.area)


OUTPUT_COLUMNS: list[OutputColumn] = [
    OutputColumn("رقم الحيازة", lambda p: str(p.holding_id)),
    OutputColumn("رقم الصفحة بالسجل", lambda p: p.page_number),
    OutputColumn("المديريه", lambda p: p.directorate),
    OutputColumn("الأداره", lambda p: p.administration),
    OutputColumn("اسم الحوض", lambda p: p.basin.name),
    OutputColumn("كود الحوض", lambda p: p.basin.code),
    OutputColumn("اسم الحائز", lambda p: p.holder.name),
    OutputColumn("الرقم القومي", lambda p: p.holder.national_id, is_text_national_id=True),
    OutputColumn("الحد الشرقى", lambda p: p.borders.east),
    OutputColumn("الحد القبلى", lambda p: p.borders.south),
    OutputColumn("الحد الغربى", lambda p: p.borders.west),
    OutputColumn("الحد البحرى", lambda p: p.borders.north),
    OutputColumn("رقم الأرض", lambda p: p.land_number),
    OutputColumn("فدان", lambda p: p.area.feddan, is_numeric=True),
    OutputColumn("قيراط", lambda p: p.area.qirat, is_numeric=True),
    OutputColumn("سهم", lambda p: p.area.sahm, is_numeric=True),
    OutputColumn("إجمالي المساحة (م²)", _total_sqm, is_numeric=True),
]
