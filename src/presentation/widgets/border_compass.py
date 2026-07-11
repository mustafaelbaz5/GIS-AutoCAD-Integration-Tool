"""Spatial 4-directional border view (compass rose), per Task C §6.4.C."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.domain.entities.borders import Borders
from src.presentation.i18n.ar import (
    BORDER_EAST_LABEL,
    BORDER_NORTH_LABEL,
    BORDER_SOUTH_LABEL,
    BORDER_WEST_LABEL,
    EMPTY_VALUE_PLACEHOLDER,
    PARCEL_CENTER_ICON,
)


class BorderCompass(QWidget):
    """Displays a parcel's four borders positioned like a small map.

    North on top, South on bottom, East on the right, West on the left
    — per §6.3's layout. A border cell that holds a neighbor's holder
    name (rather than a fixed landmark) is clickable; the caller
    decides whether a match exists (`neighbor_clicked` just reports the
    raw border text).
    """

    neighbor_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._north_button = self._make_border_button()
        self._south_button = self._make_border_button()
        self._east_button = self._make_border_button()
        self._west_button = self._make_border_button()
        self._center_label = QLabel(PARCEL_CENTER_ICON)
        self._center_label.setProperty("card", True)

        grid = QGridLayout(self)
        grid.addWidget(self._wrap(BORDER_NORTH_LABEL, self._north_button), 0, 1)
        grid.addWidget(self._wrap(BORDER_WEST_LABEL, self._west_button), 1, 0)
        grid.addWidget(self._center_label, 1, 1)
        grid.addWidget(self._wrap(BORDER_EAST_LABEL, self._east_button), 1, 2)
        grid.addWidget(self._wrap(BORDER_SOUTH_LABEL, self._south_button), 2, 1)

    def display(self, borders: Borders, center_text: str) -> None:
        """Show `borders`' four values, with `center_text` in the middle."""
        self._set_border(self._north_button, borders.north)
        self._set_border(self._south_button, borders.south)
        self._set_border(self._east_button, borders.east)
        self._set_border(self._west_button, borders.west)
        self._center_label.setText(f"{PARCEL_CENTER_ICON}\n{center_text}")

    def _set_border(self, button: QPushButton, text: str | None) -> None:
        button.setText(text or EMPTY_VALUE_PLACEHOLDER)
        button.setEnabled(bool(text))

    def _make_border_button(self) -> QPushButton:
        button = QPushButton(EMPTY_VALUE_PLACEHOLDER)
        button.setFlat(True)
        button.setEnabled(False)
        button.setProperty("iconButton", True)
        button.clicked.connect(lambda: self.neighbor_clicked.emit(button.text()))
        return button

    def _wrap(self, label_text: str, button: QPushButton) -> QFrame:
        frame = QFrame()
        frame.setProperty("card", True)
        layout = QVBoxLayout(frame)
        title = QLabel(label_text)
        title.setProperty("secondary", True)
        layout.addWidget(title)
        layout.addWidget(button)
        return frame
