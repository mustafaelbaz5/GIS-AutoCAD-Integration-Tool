"""Tests for SearchHoldingsUseCase, using hand-crafted Parcel fixtures."""

from src.application.use_cases.search_holdings_use_case import SearchHoldingsUseCase
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId


def make_parcel(
    holding_id: str,
    holder_name: str | None,
    land_number: str | None = "1",
) -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number=None,
        directorate=None,
        administration=None,
        basin=Basin(name="basin", code=None),
        holder=Holder(name=holder_name, national_id=None),
        borders=Borders(east=None, south=None, west=None, north=None),
        land_number=land_number,
        area=Area(None, None, None),
    )


def test_numeric_query_matches_holding_id_by_prefix() -> None:
    parcels = [make_parcel("992", "H1"), make_parcel("884", "H2")]

    matches = SearchHoldingsUseCase().execute(parcels, "99")

    assert len(matches) == 1
    assert matches[0].holding_id == "992"


def test_numeric_query_falls_back_to_contains_match() -> None:
    parcels = [make_parcel("1992", "H1")]

    matches = SearchHoldingsUseCase().execute(parcels, "99")

    assert len(matches) == 1
    assert matches[0].holding_id == "1992"


def test_prefix_match_ranks_above_contains_match() -> None:
    parcels = [make_parcel("1992", "H1"), make_parcel("992", "H2")]

    matches = SearchHoldingsUseCase().execute(parcels, "99")

    assert matches[0].holding_id == "992"


def test_text_query_fuzzy_matches_holder_name_after_normalization() -> None:
    parcels = [make_parcel("1", "محمد أحمد الشحاتي"), make_parcel("2", "سالم علي")]

    matches = SearchHoldingsUseCase().execute(parcels, "محمد احمد الشحاتى")

    assert len(matches) == 1
    assert matches[0].holding_id == "1"


def test_text_query_excludes_matches_below_threshold() -> None:
    parcels = [make_parcel("1", "شيء مختلف تماما عن الاسم")]

    matches = SearchHoldingsUseCase().execute(parcels, "محمد أحمد")

    assert matches == []


def test_results_are_limited_to_max_results() -> None:
    parcels = [make_parcel(str(i), "1") for i in range(15)]

    matches = SearchHoldingsUseCase().execute(parcels, "1", max_results=5)

    assert len(matches) == 5


def test_empty_query_returns_no_matches() -> None:
    parcels = [make_parcel("1", "H1")]

    assert SearchHoldingsUseCase().execute(parcels, "") == []
    assert SearchHoldingsUseCase().execute(parcels, "   ") == []


def test_groups_multiple_parcels_under_the_same_holding_id() -> None:
    parcels = [
        make_parcel("100", "محمد أحمد", land_number="1"),
        make_parcel("100", "محمد أحمد", land_number="2"),
    ]

    matches = SearchHoldingsUseCase().execute(parcels, "100")

    assert len(matches) == 1
    assert len(matches[0].parcels) == 2
    assert {p.land_number for p in matches[0].parcels} == {"1", "2"}


def test_holder_name_with_no_name_never_matches_text_search() -> None:
    parcels = [make_parcel("1", None)]

    matches = SearchHoldingsUseCase().execute(parcels, "محمد")

    assert matches == []


def test_find_best_name_match_returns_the_top_scoring_parcel() -> None:
    parcels = [make_parcel("1", "محمد أحمد الشحات"), make_parcel("2", "سالم علي")]

    result = SearchHoldingsUseCase().find_best_name_match(parcels, "محمد أحمد الشحات")

    assert result is not None
    assert str(result.holding_id) == "1"


def test_find_best_name_match_returns_none_below_threshold() -> None:
    parcels = [make_parcel("1", "شيء مختلف تماما")]

    result = SearchHoldingsUseCase().find_best_name_match(parcels, "محمد أحمد")

    assert result is None


def test_find_best_name_match_returns_none_for_empty_dataset() -> None:
    result = SearchHoldingsUseCase().find_best_name_match([], "محمد أحمد")

    assert result is None
