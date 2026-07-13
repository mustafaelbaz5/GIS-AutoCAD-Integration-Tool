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
    # Row 1 (East->West): 1 <- 2, vertical drop via 2's south (القبلي) to 3.
    # Row 2 (West->East, direction flipped): 3 -> 4, no vertical match from
    # 4 so the chain resumes arbitrarily with the one remaining parcel, 5.
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="H2")
    p2 = make_parcel("2", "H2", west="مصرف", south="H3")
    p3 = make_parcel("3", "H3", east="H4")
    p4 = make_parcel("4", "H4", east="مروى رى")
    p5 = make_parcel("5", "H5", west="غير موجود")

    result = SpatialSorter(LANDMARKS).sort([p1, p4, p2, p5, p3])

    assert [str(p.holding_id) for p in result.parcels] == ["1", "2", "3", "4", "5"]
    assert any("resumed from an arbitrary remaining parcel" in w for w in result.warnings)
    assert result.unplaced_count == 1


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


def test_boustrophedon_six_parcel_diagram_matches_brief_section_3_1() -> None:
    # Row 1 (East->West): 1 <- 2 <- 3, then drop via 3's south (القبلي) to 4.
    # Row 2 (West->East, direction flipped): 4 -> 5 -> 6.
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="H2")
    p2 = make_parcel("2", "H2", west="H3")
    p3 = make_parcel("3", "H3", west="مصرف", south="H4")
    p4 = make_parcel("4", "H4", east="H5")
    p5 = make_parcel("5", "H5", east="H6")
    p6 = make_parcel("6", "H6", east="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p1, p3, p6, p4, p2, p5])

    assert [str(p.holding_id) for p in result.parcels] == ["1", "2", "3", "4", "5", "6"]
    assert result.unplaced_count == 0


def test_vertical_lookup_falls_back_to_north_when_south_has_no_match() -> None:
    # Single-parcel row 1 ends immediately (both borders are landmarks);
    # its south text matches nobody, so the algorithm must fall back to
    # its north text, which does match — not to the arbitrary-resume path.
    p_a = make_parcel("A", "HA", east="مصرف صرف", west="مصرف", south="غير موجود ابدا", north="HB")
    p_b = make_parcel("B", "HB", east="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p_a, p_b])

    assert [str(p.holding_id) for p in result.parcels] == ["A", "B"]
    assert result.unplaced_count == 0
    assert not any("resumed from an arbitrary remaining parcel" in w for w in result.warnings)


def test_direction_alternates_across_three_or_more_rows() -> None:
    # Row 1 (East->West): 1 <- 2.       Row 2 (West->East): 3 -> 4.
    # Row 3 (East->West again): 5 <- 6. Each row's horizontal chain only
    # succeeds if the direction used to read borders is the expected one
    # for that row, so a wrong (non-alternating) direction would leave
    # rows 2/3 unable to extend past their first parcel.
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="H2")
    p2 = make_parcel("2", "H2", west="مصرف", south="H3")
    p3 = make_parcel("3", "H3", east="H4")
    p4 = make_parcel("4", "H4", east="مروى رى", south="H5")
    p5 = make_parcel("5", "H5", west="H6")
    p6 = make_parcel("6", "H6", west="ترعة رى")

    result = SpatialSorter(LANDMARKS).sort([p1, p4, p6, p3, p5, p2])

    assert [str(p.holding_id) for p in result.parcels] == ["1", "2", "3", "4", "5", "6"]
    assert result.unplaced_count == 0


def test_landmark_matching_is_normalized() -> None:
    p1 = make_parcel("1", "H1", east="مصرف صرف", west="مصرف")

    result = SpatialSorter(LANDMARKS).sort([p1])

    assert [str(p.holding_id) for p in result.parcels] == ["1"]
    assert not any("No starting parcel" in w for w in result.warnings)
