"""A single statistic tile, per Iteration 2 §4.2/4.3.

Uses theme QSS properties (`statValue`, `statVariant`, `iconButton`)
rather than inline styling, per Iteration 2's theming rule.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.presentation.i18n.ar import COPY_VALUE_TOOLTIP


class StatCard(QFrame):
    """One stat tile: icon + large value + label, with copy-to-clipboard.

    Args:
        icon: A single emoji/glyph shown at the top-right of the card.
        label: The Arabic metric label, shown small and muted.
        value_text: The already-formatted value to display and copy.
        variant: "neutral" (default), "success", or "warning" — selects
            the value color via the `statVariant` QSS property.
        clickable: When True, the card emits `clicked` on mouse press
            and shows a pointing-hand cursor — used for stats that
            represent a navigable subset of rows (e.g. incomplete rows).
    """

    clicked = Signal()

    def __init__(
        self,
        icon: str,
        label: str,
        value_text: str,
        variant: str = "neutral",
        clickable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setProperty("statVariant", variant)
        self._clickable = clickable
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._value_text = value_text

        icon_label = QLabel(icon)
        value_label = QLabel(value_text)
        value_label.setProperty("statValue", True)
        value_label.setWordWrap(True)

        text_label = QLabel(label)
        text_label.setProperty("secondary", True)
        text_label.setWordWrap(True)

        copy_button = QPushButton("⧉")
        copy_button.setProperty("iconButton", True)
        copy_button.setToolTip(COPY_VALUE_TOOLTIP)
        copy_button.setFixedWidth(28)
        copy_button.clicked.connect(self._copy_value)

        header_row = QHBoxLayout()
        header_row.addWidget(icon_label)
        header_row.addStretch()
        header_row.addWidget(copy_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_row)
        layout.addWidget(value_label)
        layout.addWidget(text_label)

    def _copy_value(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._value_text)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if self._clickable:
            self.clicked.emit()
