"""Land parcel entity — the central aggregate of the domain."""

from dataclasses import dataclass

from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId


@dataclass(frozen=True)
class Parcel:
    """A single agricultural land-holding parcel.

    Aggregates identity (holding ID), location (basin, borders), the
    holder, and the area. This is the output schema's row, minus the
    computed total-area column which is derived on demand via
    :class:`src.domain.services.area_calculator.AreaCalculator`.
    """

    holding_id: HoldingId
    page_number: str | None
    """رقم الصفحة بالسجل"""

    directorate: str | None
    """المديريه"""

    administration: str | None
    """الأداره"""

    basin: Basin
    holder: Holder
    borders: Borders

    land_number: str | None
    """رقم الأرض"""

    area: Area
