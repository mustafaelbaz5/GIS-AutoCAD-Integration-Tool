"""Tests for MergeParcelsUseCase, using fake ports (no real Excel I/O)."""

import pytest
from src.application.dto.parcel_record import ParcelRecord
from src.application.exceptions import PipelineCancelledError
from src.application.ports.data_source_port import DataSourcePort
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.domain.services.spatial_sorter import SpatialSorter


class FakeDataSource(DataSourcePort):
    def __init__(self, records: list[ParcelRecord]) -> None:
        self._records = records

    def read(self) -> list[ParcelRecord]:
        return self._records


def make_record(
    holding_id_raw: str | None = "1",
    page_number: str | None = None,
    directorate: str | None = None,
    administration: str | None = None,
    basin_name: str | None = None,
    basin_code: str | None = None,
    holder_name: str | None = None,
    national_id: str | None = None,
    east: str | None = None,
    south: str | None = None,
    west: str | None = None,
    north: str | None = None,
    land_number: str | None = None,
    feddan: float | None = None,
    qirat: float | None = None,
    sahm: float | None = None,
) -> ParcelRecord:
    return ParcelRecord(
        holding_id_raw=holding_id_raw,
        page_number=page_number,
        directorate=directorate,
        administration=administration,
        basin_name=basin_name,
        basin_code=basin_code,
        holder_name=holder_name,
        national_id=national_id,
        east=east,
        south=south,
        west=west,
        north=north,
        land_number=land_number,
        feddan=feddan,
        qirat=qirat,
        sahm=sahm,
    )


def test_merges_base_and_secondary_by_holding_id() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", holder_name="Base Holder")])
    secondary = FakeDataSource([make_record(holding_id_raw="1", national_id="12345678901234")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert len(result.parcels) == 1
    assert result.parcels[0].holder.name == "Base Holder"
    assert result.parcels[0].holder.national_id == "12345678901234"


def test_prefers_base_value_over_secondary_for_shared_fields() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", holder_name="Base Holder")])
    secondary = FakeDataSource([make_record(holding_id_raw="1", holder_name="Secondary Holder")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].holder.name == "Base Holder"


def test_falls_back_to_secondary_when_base_field_missing() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", holder_name=None)])
    secondary = FakeDataSource([make_record(holding_id_raw="1", holder_name="Secondary Holder")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].holder.name == "Secondary Holder"


def test_national_id_prefers_primary_when_present() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", national_id="primary-id")])
    secondary = FakeDataSource([make_record(holding_id_raw="1", national_id="supplementary-id")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].holder.national_id == "primary-id"


def test_national_id_falls_back_to_supplementary_when_primary_missing() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", national_id=None)])
    secondary = FakeDataSource([make_record(holding_id_raw="1", national_id="supplementary-id")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].holder.national_id == "supplementary-id"


def test_borders_and_land_number_are_base_only_never_secondary() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", east="Base East", land_number="B1")])
    secondary = FakeDataSource(
        [make_record(holding_id_raw="1", east="Secondary East", land_number="S1")]
    )

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].borders.east == "Base East"
    assert result.parcels[0].land_number == "B1"


def test_base_row_without_secondary_match_keeps_base_only_data() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", holder_name="Solo Holder")])
    secondary = FakeDataSource([])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert len(result.parcels) == 1
    assert result.parcels[0].holder.name == "Solo Holder"
    assert result.parcels[0].holder.national_id is None


def test_secondary_only_row_does_not_create_a_new_parcel() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1")])
    secondary = FakeDataSource([make_record(holding_id_raw="1"), make_record(holding_id_raw="999")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert len(result.parcels) == 1


def test_missing_fields_in_both_sources_remain_empty_not_fabricated() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1", basin_code=None)])
    secondary = FakeDataSource([make_record(holding_id_raw="1", basin_code=None)])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].basin.code is None


def test_join_key_matches_across_leading_zero_variants() -> None:
    base = FakeDataSource([make_record(holding_id_raw="010", holder_name="Base Holder")])
    secondary = FakeDataSource([make_record(holding_id_raw="10", national_id="matched")])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert result.parcels[0].holder.national_id == "matched"


def test_base_row_without_holding_id_is_skipped_with_warning() -> None:
    base = FakeDataSource([make_record(holding_id_raw=None), make_record(holding_id_raw="1")])
    secondary = FakeDataSource([])

    result = MergeParcelsUseCase(base, secondary).execute()

    assert len(result.parcels) == 1
    assert any("Skipped" in w for w in result.warnings)


def test_spatial_sorter_is_applied_when_provided() -> None:
    base = FakeDataSource(
        [
            make_record(
                holding_id_raw="1",
                holder_name="H1",
                basin_name="basin",
                east="مصرف صرف",
                west="H2",
            ),
            make_record(holding_id_raw="2", holder_name="H2", basin_name="basin", west="مصرف"),
        ]
    )
    secondary = FakeDataSource([])
    sorter = SpatialSorter(landmark_keywords=["مصرف صرف", "مصرف"])

    result = MergeParcelsUseCase(base, secondary, spatial_sorter=sorter).execute()

    assert [str(p.holding_id) for p in result.parcels] == ["1", "2"]


def test_reports_progress_from_zero_to_hundred() -> None:
    base = FakeDataSource([make_record(holding_id_raw=str(i)) for i in range(1, 6)])
    secondary = FakeDataSource([])
    events: list[tuple[int, str]] = []

    MergeParcelsUseCase(base, secondary).execute(on_progress=lambda p, m: events.append((p, m)))

    assert events[0] == (0, "Reading primary source...")
    assert events[-1][0] == 100


def test_raises_cancelled_error_when_cancellation_requested_immediately() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1")])
    secondary = FakeDataSource([])

    with pytest.raises(PipelineCancelledError):
        MergeParcelsUseCase(base, secondary).execute(is_cancelled=lambda: True)


def test_does_not_raise_when_never_cancelled() -> None:
    base = FakeDataSource([make_record(holding_id_raw="1")])
    secondary = FakeDataSource([])

    result = MergeParcelsUseCase(base, secondary).execute(is_cancelled=lambda: False)

    assert len(result.parcels) == 1
