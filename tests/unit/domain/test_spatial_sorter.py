"""Tests for SpatialSorter, per project brief §5.5."""

from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.services.spatial_sorter import SpatialSorter
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId

LANDMARKS = ["مصرف صرف", "مروى طريق", "طريق ترعة رى", "مصرف", "مروى رى", "ترعة رى"]


def make_parcel(
    holding_id: str,
    holder_name: str,
    basin_name: str = "basin",
    east: str | None = None,
    south: str | None = None,
    west: str | None = None,
    north: str | None = None,
) -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number=None,
        directorate=None,
        administration=None,
        basin=Basin(name=basin_name, code=None),
        holder=Holder(name=holder_name, national_id=None),
        borders=Borders(east=east, south=south, west=west, north=north),
        land_number=None,
        area=Area(None, None, None),
    )


def test_sorts_five_parcel_basin_with_horizontal_and_vertical_chains() -> None:
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="H2", north="H3")
    p2 = make_parcel("2", "H2", west="مصرف")
    p3 = make_parcel("3", "H3", west="H4")
    p4 = make_parcel("4", "H4", west="مروى رى")
    p5 = make_parcel("5", "H5", west="غير موجود")

    result = SpatialSorter(LANDMARKS).sort([p4, p2, p5, p1, p3])

    assert [str(p.holding_id) for p in result.parcels] == ["1", "2", "3", "4", "5"]
    assert any("could not be placed" in w for w in result.warnings)


def test_never_drops_a_parcel_even_when_unplaceable() -> None:
    p1 = make_parcel("1", "H1", east="مصرف", west="مصرف")
    orphan = make_parcel("2", "H2", west="لا يوجد تطابق")

    result = SpatialSorter(LANDMARKS).sort([p1, orphan])

    assert len(result.parcels) == 2
    assert {str(p.holding_id) for p in result.parcels} == {"1", "2"}
    assert result.unplaced_count == 1


def test_unplaced_count_is_zero_when_everything_placed() -> None:
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p1])

    assert result.unplaced_count == 0


def test_missing_starting_landmark_falls_back_to_arbitrary_start_with_warning() -> None:
    p1 = make_parcel("1", "H1", west="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p1])

    assert [str(p.holding_id) for p in result.parcels] == ["1"]
    assert any("No starting parcel" in w for w in result.warnings)


def test_unmatched_western_neighbor_ends_row_with_warning() -> None:
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="غير موجود ابدا")

    result = SpatialSorter(LANDMARKS).sort([p1])

    assert [str(p.holding_id) for p in result.parcels] == ["1"]
    assert any("No western neighbor found" in w for w in result.warnings)


def test_basins_are_sorted_independently() -> None:
    a1 = make_parcel("a1", "A1", basin_name="A", east="مصرف", west="مصرف")
    b1 = make_parcel("b1", "B1", basin_name="B", east="مصرف صرف", west="مصرف")

    result = SpatialSorter(LANDMARKS).sort([b1, a1])

    holding_ids = {str(p.holding_id) for p in result.parcels}
    assert holding_ids == {"a1", "b1"}


def test_landmark_matching_is_normalized() -> None:
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p1])

    assert [str(p.holding_id) for p in result.parcels] == ["1"]
    assert not any("No starting parcel" in w for w in result.warnings)
