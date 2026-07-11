"""Drag-and-drop file input zone, per project brief §7.3."""

from pathlib import Path

import openpyxl
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QVBoxLayout, QWidget

from src.presentation.i18n.ar import DROP_PLACEHOLDER, FILE_READ_ERROR, INVALID_FILE_TYPE


class DropZone(QFrame):
    """A labeled area that accepts a dropped `.xlsx` file, or a click to browse.

    Performs lightweight validation on selection (file extension, and
    that the workbook opens with a readable row count) — the
    authoritative read still happens later via the infrastructure
    readers; this is purely UX feedback per brief §7.4.
    """

    file_selected = Signal(str)

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._title_label = QLabel(title)
        self._status_label = QLabel(DROP_PLACEHOLDER)
        self._status_label.setProperty("secondary", True)
        self._status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._status_label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        self._handle_selected_path(urls[0].toLocalFile())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        path, _ = QFileDialog.getOpenFileName(self, filter="Excel Files (*.xlsx)")
        if path:
            self._handle_selected_path(path)

    def _handle_selected_path(self, path: str) -> None:
        if not path.lower().endswith(".xlsx"):
            self.set_error(INVALID_FILE_TYPE)
            return

        row_count = self._peek_row_count(path)
        if row_count is None:
            self.set_error(FILE_READ_ERROR)
            return

        self.set_selected(Path(path).name, row_count)
        self.file_selected.emit(path)

    def _peek_row_count(self, path: str) -> int | None:
        try:
            workbook = openpyxl.load_workbook(path, read_only=True)
            sheet = workbook.active
            return sheet.max_row if sheet is not None else None
        except Exception:
            return None

    def set_selected(self, filename: str, row_count: int) -> None:
        self._status_label.setText(f"✔ {filename} — {row_count} صف")

    def set_error(self, message: str) -> None:
        self._status_label.setText(f"✖ {message}")

    def reset(self) -> None:
        self._status_label.setText(DROP_PLACEHOLDER)
