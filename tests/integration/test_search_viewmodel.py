"""Tests for SearchViewModel, using a fake OutputFileSourcePort (no real I/O)."""

from pathlib import Path

from PySide6.QtWidgets import QApplication
from src.application.dto.search_result import SearchMatch
from src.application.ports.output_file_source_port import OutputFileSourcePort
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId
from src.infrastructure.excel.output_file_reader import OutputFileFormatError
from src.presentation.viewmodels.search_viewmodel import SearchViewModel


def make_parcel(holding_id: str, holder_name: str | None = "Holder") -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number=None,
        directorate=None,
        administration=None,
        basin=Basin(name="basin", code=None),
        holder=Holder(name=holder_name, national_id=None),
        borders=Borders(east="Neighbor", south=None, west=None, north=None),
        land_number="1",
        area=Area(None, None, None),
    )


class FakeReader(OutputFileSourcePort):
    def __init__(self, parcels: list[Parcel] | None = None, error: Exception | None = None) -> None:
        self._parcels = parcels or []
        self._error = error

    def read(self, path: Path) -> list[Parcel]:
        if self._error is not None:
            raise self._error
        return self._parcels


def test_load_file_success_emits_file_loaded(qapp: QApplication) -> None:
    reader = FakeReader([make_parcel("1")])
    viewmodel = SearchViewModel(reader)
    events: list[tuple[str, int]] = []
    viewmodel.file_loaded.connect(lambda path, count: events.append((path, count)))

    viewmodel.load_file(Path("/fake/output.xlsx"))

    assert viewmodel.is_loaded is True
    assert events == [(str(Path("/fake/output.xlsx")), 1)]


def test_load_file_malformed_emits_load_error(qapp: QApplication) -> None:
    reader = FakeReader(error=OutputFileFormatError(["المديريه"]))
    viewmodel = SearchViewModel(reader)
    errors: list[str] = []
    viewmodel.load_error.connect(errors.append)

    viewmodel.load_file(Path("/fake/output.xlsx"))

    assert viewmodel.is_loaded is False
    assert len(errors) == 1
    assert "المديريه" in errors[0]


def test_load_file_generic_failure_emits_friendly_error_not_raw_exception(
    qapp: QApplication,
) -> None:
    reader = FakeReader(error=ValueError("some raw technical detail"))
    viewmodel = SearchViewModel(reader)
    errors: list[str] = []
    viewmodel.load_error.connect(errors.append)

    viewmodel.load_file(Path("/fake/output.xlsx"))

    assert len(errors) == 1
    assert "some raw technical detail" not in errors[0]


def test_search_emits_matches_changed(qapp: QApplication) -> None:
    reader = FakeReader([make_parcel("100", "محمد أحمد")])
    viewmodel = SearchViewModel(reader)
    viewmodel.load_file(Path("/fake/output.xlsx"))
    matches_events = []
    viewmodel.matches_changed.connect(matches_events.append)

    viewmodel.search("100")

    assert len(matches_events) == 1
    assert matches_events[0][0].holding_id == "100"


def test_select_match_with_single_parcel_emits_parcel_selected(qapp: QApplication) -> None:
    parcel = make_parcel("1")
    reader = FakeReader([parcel])
    viewmodel = SearchViewModel(reader)
    viewmodel.load_file(Path("/fake/output.xlsx"))
    selected: list[Parcel] = []
    viewmodel.parcel_selected.connect(selected.append)
    match = SearchMatch(holding_id="1", holder_name="H", parcels=[parcel], score=100)

    viewmodel.select_match(match)

    assert selected == [parcel]


def test_select_match_with_multiple_parcels_emits_parcels_available(qapp: QApplication) -> None:
    parcels = [make_parcel("1"), make_parcel("1")]
    viewmodel = SearchViewModel(FakeReader(parcels))
    available: list[list[Parcel]] = []
    viewmodel.parcels_available.connect(available.append)

    viewmodel.select_match(SearchMatch(holding_id="1", holder_name="H", parcels=parcels, score=100))

    assert available == [parcels]


def test_navigate_to_neighbor_finds_and_selects_match(qapp: QApplication) -> None:
    reader = FakeReader([make_parcel("1", "محمد أحمد الشحات")])
    viewmodel = SearchViewModel(reader)
    viewmodel.load_file(Path("/fake/output.xlsx"))
    selected: list[Parcel] = []
    viewmodel.parcel_selected.connect(selected.append)

    viewmodel.navigate_to_neighbor("محمد أحمد الشحات")

    assert len(selected) == 1
    assert str(selected[0].holding_id) == "1"


def test_navigate_to_neighbor_is_a_noop_when_no_match(qapp: QApplication) -> None:
    reader = FakeReader([make_parcel("1", "شخص آخر تماما")])
    viewmodel = SearchViewModel(reader)
    viewmodel.load_file(Path("/fake/output.xlsx"))
    selected: list[Parcel] = []
    viewmodel.parcel_selected.connect(selected.append)

    viewmodel.navigate_to_neighbor("مصرف صرف")

    assert selected == []
