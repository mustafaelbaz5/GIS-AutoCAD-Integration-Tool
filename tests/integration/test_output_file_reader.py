"""Integration tests for OutputFileReader: round-trips a small sample
written by ProfessionalExcelWriter, per Iteration 2 Task C.
"""

from pathlib import Path

import openpyxl
import pytest
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId
from src.infrastructure.excel.output_file_reader import OutputFileFormatError, OutputFileReader
from src.infrastructure.excel.professional_excel_writer import ProfessionalExcelWriter


def make_parcel(
    holding_id: str,
    holder_name: str | None = "Holder",
    national_id: str | None = "12345678901234",
    basin_name: str | None = "Basin A",
    feddan: float | None = 1.0,
    qirat: float | None = 2.0,
    sahm: float | None = 3.0,
    east: str | None = "East neighbor",
) -> Parcel:
    return Parcel(
        holding_id=HoldingId(holding_id),
        page_number="1",
        directorate="Dir",
        administration="Admin",
        basin=Basin(name=basin_name, code="10"),
        holder=Holder(name=holder_name, national_id=national_id),
        borders=Borders(east=east, south="South", west="West", north="North"),
        land_number="L1",
        area=Area(feddan=feddan, qirat=qirat, sahm=sahm),
    )


def test_round_trips_parcels_written_by_the_writer(tmp_path: Path) -> None:
    output_path = tmp_path / "output.xlsx"
    original = [make_parcel("010", holder_name="Some Holder"), make_parcel("2", basin_name="B")]
    ProfessionalExcelWriter().write(original, output_path)

    read_back = OutputFileReader().read(output_path)

    assert len(read_back) == 2
    holding_ids = {str(p.holding_id) for p in read_back}
    assert holding_ids == {"010", "2"}


def test_preserves_field_values_through_round_trip(tmp_path: Path) -> None:
    output_path = tmp_path / "output.xlsx"
    parcel = make_parcel("1", holder_name="Ahmed", national_id="01234567890123")
    ProfessionalExcelWriter().write([parcel], output_path)

    read_back = OutputFileReader().read(output_path)

    assert len(read_back) == 1
    parcel = read_back[0]
    assert parcel.holder.name == "Ahmed"
    assert parcel.holder.national_id == "01234567890123"
    assert parcel.area.feddan == 1.0
    assert parcel.area.qirat == 2.0
    assert parcel.area.sahm == 3.0
    assert parcel.borders.east == "East neighbor"


def test_skips_blank_separator_rows_and_totals_row(tmp_path: Path) -> None:
    output_path = tmp_path / "output.xlsx"
    parcels = [make_parcel("1", basin_name="A"), make_parcel("2", basin_name="B")]
    ProfessionalExcelWriter().write(parcels, output_path)

    read_back = OutputFileReader().read(output_path)

    assert len(read_back) == 2  # separator row + totals row correctly skipped


def test_raises_format_error_when_columns_are_missing(tmp_path: Path) -> None:
    output_path = tmp_path / "malformed.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["رقم الحيازة", "اسم الحائز"])  # missing most expected columns
    sheet.append(["1", "Someone"])
    workbook.save(output_path)

    with pytest.raises(OutputFileFormatError) as exc_info:
        OutputFileReader().read(output_path)

    assert "المديريه" in exc_info.value.missing_headers
    assert "الرقم القومي" in exc_info.value.missing_headers
