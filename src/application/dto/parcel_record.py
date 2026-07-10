"""Raw parcel data DTO, as read from a single source (before merging)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParcelRecord:
    """A single source's view of one parcel row.

    Produced by `DataSourcePort.read()` implementations (base or
    secondary file readers). Fields are optional because neither source
    populates the full output schema on its own — the merge use case
    combines two `ParcelRecord`s per the fill-priority rules in the
    project brief §5.4.
    """

    holding_id_raw: str | None
    """رقم الحيازة (base) or رقم حيازه 2022 (secondary) — the join key."""

    page_number: str | None
    directorate: str | None
    administration: str | None
    basin_name: str | None
    basin_code: str | None
    holder_name: str | None
    national_id: str | None
    east: str | None
    south: str | None
    west: str | None
    north: str | None
    land_number: str | None
    feddan: float | None
    qirat: float | None
    sahm: float | None
