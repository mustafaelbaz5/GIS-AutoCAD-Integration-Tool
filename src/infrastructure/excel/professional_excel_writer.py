"""Professional Excel writer for the final merged output, per §8."""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from src.application.ports.data_sink_port import DataSinkPort
from src.domain.entities.parcel import Parcel
from src.domain.services.area_calculator import AreaCalculator
from src.infrastructure.excel.output_schema import OUTPUT_COLUMNS

_HEADER_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
_HEADER_FONT = Font(color="F1F5F9", bold=True)
_HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center")

_THIN_SIDE = Side(style="thin", color="CBD5E1")
_THIN_BORDER = Border(left=_THIN_SIDE, right=_THIN_SIDE, top=_THIN_SIDE, bottom=_THIN_SIDE)

_BAND_FILL_A = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
_BAND_FILL_B = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

_NUMBER_FORMAT = "0.00"
_TEXT_FORMAT = "@"
_TOTALS_LABEL = "الإجمالي"
_SHEET_TITLE = "البيانات المجمعة"

_NO_BASIN_YET: object = object()


def default_output_filename(now: datetime | None = None) -> str:
    """Return the timestamped default filename, per §8.1."""
    timestamp = (now or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
    return f"merged_output_{timestamp}.xlsx"


class ProfessionalExcelWriter(DataSinkPort):
    """Writes the final merged parcel list as a formatted .xlsx file.

    Implements the formatting rules of project brief §8: styled header,
    RTL sheet direction, frozen header row, thin borders, banded fill
    per basin block with a blank separator row between basins, and a
    totals row.
    """

    def write(self, parcels: Sequence[Parcel], output_path: Path) -> None:
        """Write `parcels` to `output_path` as a formatted .xlsx file."""
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = _SHEET_TITLE
        worksheet.sheet_view.rightToLeft = True

        self._write_header(worksheet)
        last_row = self._write_data_rows(worksheet, parcels)
        self._write_totals_row(worksheet, last_row, parcels)
        self._autofit_columns(worksheet, parcels)
        worksheet.freeze_panes = "A2"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_path)

    def _write_header(self, worksheet: Worksheet) -> None:
        for col_index, column in enumerate(OUTPUT_COLUMNS, start=1):
            cell = worksheet.cell(row=1, column=col_index, value=column.header)
            cell.fill = _HEADER_FILL
            cell.font = _HEADER_FONT
            cell.alignment = _HEADER_ALIGNMENT
            cell.border = _THIN_BORDER

    def _write_data_rows(self, worksheet: Worksheet, parcels: Sequence[Parcel]) -> int:
        row_index = 2
        current_basin: object = _NO_BASIN_YET
        band_toggle = False

        for parcel in parcels:
            basin_key = parcel.basin.name
            if basin_key != current_basin:
                if current_basin is not _NO_BASIN_YET:
                    row_index += 1  # blank separator row between basin blocks
                current_basin = basin_key
                band_toggle = not band_toggle
            self._write_row(worksheet, row_index, parcel, band_toggle)
            row_index += 1

        return row_index - 1

    def _write_row(
        self, worksheet: Worksheet, row_index: int, parcel: Parcel, band_toggle: bool
    ) -> None:
        fill = _BAND_FILL_B if band_toggle else _BAND_FILL_A
        for col_index, column in enumerate(OUTPUT_COLUMNS, start=1):
            cell = worksheet.cell(row=row_index, column=col_index, value=column.getter(parcel))
            cell.fill = fill
            cell.border = _THIN_BORDER
            if column.is_numeric:
                cell.number_format = _NUMBER_FORMAT
            elif column.is_text_national_id:
                cell.number_format = _TEXT_FORMAT

    def _write_totals_row(
        self, worksheet: Worksheet, last_data_row: int, parcels: Sequence[Parcel]
    ) -> None:
        row_index = last_data_row + 1
        totals = self._compute_totals(parcels)

        label_cell = worksheet.cell(row=row_index, column=1, value=_TOTALS_LABEL)
        label_cell.font = Font(bold=True)
        label_cell.border = _THIN_BORDER

        for col_index, column in enumerate(OUTPUT_COLUMNS, start=1):
            if column.header not in totals:
                continue
            cell = worksheet.cell(row=row_index, column=col_index, value=totals[column.header])
            cell.font = Font(bold=True)
            cell.border = _THIN_BORDER
            cell.number_format = _NUMBER_FORMAT

    def _compute_totals(self, parcels: Sequence[Parcel]) -> dict[str, float]:
        feddan_total = sum(p.area.feddan or 0.0 for p in parcels)
        qirat_total = sum(p.area.qirat or 0.0 for p in parcels)
        sahm_total = sum(p.area.sahm or 0.0 for p in parcels)
        sqm_total = sum(AreaCalculator.calculate_total_sqm(p.area) or 0.0 for p in parcels)
        return {
            "فدان": round(feddan_total, 2),
            "قيراط": round(qirat_total, 2),
            "سهم": round(sahm_total, 2),
            "إجمالي المساحة (م²)": round(sqm_total, 2),
        }

    def _autofit_columns(self, worksheet: Worksheet, parcels: Sequence[Parcel]) -> None:
        for col_index, column in enumerate(OUTPUT_COLUMNS, start=1):
            max_length = len(column.header)
            for parcel in parcels:
                value = column.getter(parcel)
                if value is not None:
                    max_length = max(max_length, len(str(value)))
            worksheet.column_dimensions[get_column_letter(col_index)].width = max_length + 4
