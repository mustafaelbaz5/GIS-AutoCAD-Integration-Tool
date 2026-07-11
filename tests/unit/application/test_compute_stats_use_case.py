"""Tests for ComputeStatsUseCase, using hand-crafted Parcel fixtures."""

from src.application.use_cases.compute_stats_use_case import ComputeStatsUseCase
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId


def make_parcel(
    holding_id: str,
    basin_name: str | None = "basin",
    holder_name: str | None = "Holder",
    national_id: str | None = "12345678901234",
    east: str | None = "East",
    south: str | None = "South",
    west: str | None = "West",
    north: str | None = "North",
    page_number: str | None = "1",
    directorate: str | None = "Dir",
    administration: str | None = "Admin",
    basin_code: str | None = "10",
    land_number: str | None = "L1",
    feddan: float | None = 1.0,
    qirat: float | None = 2.0,
    sahm: float | None = 3.0,
) -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number=page_number,
        directorate=directorate,
        administration=administration,
        basin=Basin(name=basin_name, code=basin_code),
        holder=Holder(name=holder_name, national_id=national_id),
        borders=Borders(east=east, south=south, west=west, north=north),
        land_number=land_number,
        area=Area(feddan=feddan, qirat=qirat, sahm=sahm),
    )


def test_counts_total_and_complete_rows() -> None:
    parcels = [make_parcel("1"), make_parcel("2")]

    stats = ComputeStatsUseCase().execute(parcels, 0, 0, 0, 1.5)

    assert stats.total_merged == 2
    assert stats.complete_rows == 2
    assert stats.incomplete_rows == 0


def test_detects_incomplete_rows_and_most_empty_fields() -> None:
    parcels = [
        make_parcel("1", holder_name=None, national_id=None),
        make_parcel("2", holder_name=None),
        make_parcel("3"),
    ]

    stats = ComputeStatsUseCase().execute(parcels, 0, 0, 0, 0.0)

    assert stats.complete_rows == 1
    assert stats.incomplete_rows == 2
    labels = [label for label, _ in stats.most_often_empty_fields]
    assert "اسم الحائز" in labels
    assert set(stats.incomplete_holding_ids) == {"1", "2"}


def test_counts_national_id_presence() -> None:
    parcels = [make_parcel("1", national_id="123"), make_parcel("2", national_id=None)]

    stats = ComputeStatsUseCase().execute(parcels, 0, 0, 0, 0.0)

    assert stats.with_national_id == 1
    assert stats.without_national_id == 1


def test_sums_feddan_and_computed_sqm() -> None:
    parcels = [
        make_parcel("1", feddan=1.0, qirat=0.0, sahm=0.0),
        make_parcel("2", feddan=2.0, qirat=0.0, sahm=0.0),
    ]

    stats = ComputeStatsUseCase().execute(parcels, 0, 0, 0, 0.0)

    assert stats.total_feddan == 3.0
    assert stats.total_sqm > 0


def test_computes_distinct_and_top_basins() -> None:
    parcels = [
        make_parcel("1", basin_name="A"),
        make_parcel("2", basin_name="A"),
        make_parcel("3", basin_name="B"),
    ]

    stats = ComputeStatsUseCase().execute(parcels, 0, 0, 0, 0.0)

    assert stats.distinct_basin_count == 2
    assert stats.top_basins[0] == ("A", 2)


def test_passes_through_side_channel_counts() -> None:
    parcels = [make_parcel("1")]

    stats = ComputeStatsUseCase().execute(
        parcels,
        primary_only_count=7,
        excluded_laghi_count=3,
        unplaced_count=5,
        elapsed_seconds=12.345,
    )

    assert stats.primary_only_count == 7
    assert stats.excluded_laghi_count == 3
    assert stats.unplaced_count == 5
    assert stats.elapsed_seconds == 12.35
    assert stats.supplementary_only_count == 0


def test_handles_empty_parcel_list() -> None:
    stats = ComputeStatsUseCase().execute([], 0, 0, 0, 0.0)

    assert stats.total_merged == 0
    assert stats.complete_rows == 0
    assert stats.incomplete_rows == 0
    assert stats.top_basins == []
