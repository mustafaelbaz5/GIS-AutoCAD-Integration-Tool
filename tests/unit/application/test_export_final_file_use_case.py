"""Tests for ExportFinalFileUseCase, using a fake sink (no real Excel I/O)."""

from collections.abc import Sequence
from pathlib import Path

import pytest
from src.application.exceptions import PipelineCancelledError
from src.application.ports.data_sink_port import DataSinkPort
from src.application.use_cases.export_final_file_use_case import ExportFinalFileUseCase
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId


class FakeDataSink(DataSinkPort):
    def __init__(self) -> None:
        self.written_parcels: Sequence[Parcel] | None = None
        self.written_path: Path | None = None

    def write(self, parcels: Sequence[Parcel], output_path: Path) -> None:
        self.written_parcels = parcels
        self.written_path = output_path


def make_parcel(holding_id: str) -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number=None,
        directorate=None,
        administration=None,
        basin=Basin(name=None, code=None),
        holder=Holder(name=None, national_id=None),
        borders=Borders(east=None, south=None, west=None, north=None),
        land_number=None,
        area=Area(None, None, None),
    )


def test_delegates_write_to_sink_with_given_parcels_and_path() -> None:
    sink = FakeDataSink()
    parcels = [make_parcel("1"), make_parcel("2")]
    output_path = Path("/tmp/output.xlsx")

    ExportFinalFileUseCase(sink).execute(parcels, output_path)

    assert sink.written_parcels == parcels
    assert sink.written_path == output_path


def test_works_with_empty_parcel_list() -> None:
    sink = FakeDataSink()

    ExportFinalFileUseCase(sink).execute([], Path("/tmp/output.xlsx"))

    assert sink.written_parcels == []


def test_reports_progress_start_and_end() -> None:
    sink = FakeDataSink()
    events: list[tuple[int, str]] = []

    ExportFinalFileUseCase(sink).execute(
        [make_parcel("1")], Path("/tmp/output.xlsx"), on_progress=lambda p, m: events.append((p, m))
    )

    assert events[0][0] == 0
    assert events[-1][0] == 100


def test_raises_cancelled_error_before_writing_when_cancelled() -> None:
    sink = FakeDataSink()

    with pytest.raises(PipelineCancelledError):
        ExportFinalFileUseCase(sink).execute(
            [make_parcel("1")], Path("/tmp/output.xlsx"), is_cancelled=lambda: True
        )

    assert sink.written_parcels is None
