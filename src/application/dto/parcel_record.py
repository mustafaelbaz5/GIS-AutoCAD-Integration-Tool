"""Raw parcel data DTO, as read from a single source (before merging)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParcelRecord:
    """A single source's view of one parcel row.

    Produced by `DataSourcePort.read()` implementations (any
    `MappedFileReader`, regardless of which slot/role it fills).
    Fields are optional because neither source populates the full
    output schema on its own — the merge use case combines a primary
    and a supplementary `ParcelRecord` per the fill-priority rules in
    the project brief §5.4.
    """

    holding_id_raw: str | None
    """The join key, per the source mapping's `join_key_column`."""

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
