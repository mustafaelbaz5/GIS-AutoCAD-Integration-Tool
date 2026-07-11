"""Tests for DropZone's file-selection validation, per project brief §7.4.

Regression coverage for a real bug: the real الاخوه.xlsx base file
lacks a proper `<dimension>` tag, so openpyxl's read-only mode reports
`sheet.max_row` as None even though the file opens and reads
perfectly fine. DropZone must not treat that as a read failure.
"""

from pathlib import Path

from PySide6.QtWidgets import QApplication
from src.presentation.widgets.drop_zone import DropZone


def test_accepts_a_valid_file_missing_dimension_metadata(
    base_file_path: Path, qapp: QApplication
) -> None:
    zone = DropZone("test")

    zone._handle_selected_path(str(base_file_path))

    assert zone._status_label.text().startswith("✔")
    assert "✖" not in zone._status_label.text()


def test_accepts_a_valid_file_with_dimension_metadata_and_shows_row_count(
    secondary_file_path: Path, qapp: QApplication
) -> None:
    zone = DropZone("test")

    zone._handle_selected_path(str(secondary_file_path))

    assert zone._status_label.text().startswith("✔")
    assert "946" in zone._status_label.text()


def test_rejects_non_xlsx_extension(tmp_path: Path, qapp: QApplication) -> None:
    zone = DropZone("test")
    bad_file = tmp_path / "not_excel.txt"
    bad_file.write_text("hello")

    zone._handle_selected_path(str(bad_file))

    assert zone._status_label.text().startswith("✖")


def test_rejects_a_genuinely_unreadable_file(tmp_path: Path, qapp: QApplication) -> None:
    zone = DropZone("test")
    fake_xlsx = tmp_path / "corrupt.xlsx"
    fake_xlsx.write_text("not a real xlsx file")

    zone._handle_selected_path(str(fake_xlsx))

    assert zone._status_label.text().startswith("✖")
