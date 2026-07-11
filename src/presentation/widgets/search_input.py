"""Autocomplete search input, per Iteration 2 Task C §6.4.A."""

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from src.application.dto.search_result import SearchMatch
from src.presentation.i18n.ar import SEARCH_PLACEHOLDER, SEARCH_RESULT_LABEL


class SearchInput(QWidget):
    """A text field with a live-filtered dropdown of `SearchMatch` results.

    Keyboard: ↑/↓ move the dropdown selection, Enter chooses the
    current item, Escape closes the dropdown — per §6.4.A.
    """

    text_changed = Signal(str)
    match_chosen = Signal(object)  # SearchMatch

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._matches: list[SearchMatch] = []

        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText(SEARCH_PLACEHOLDER)
        self._line_edit.textChanged.connect(self.text_changed.emit)
        self._line_edit.installEventFilter(self)

        self._results_list = QListWidget()
        self._results_list.setVisible(False)
        self._results_list.itemActivated.connect(self._on_item_activated)
        self._results_list.itemClicked.connect(self._on_item_activated)

        layout = QVBoxLayout(self)
        layout.addWidget(self._line_edit)
        layout.addWidget(self._results_list)

    def set_matches(self, matches: list[SearchMatch]) -> None:
        """Replace the dropdown's contents with `matches`."""
        self._matches = matches
        self._results_list.clear()
        for match in matches:
            label = SEARCH_RESULT_LABEL.format(
                name=match.holder_name or "—", holding_id=match.holding_id
            )
            self._results_list.addItem(label)
        self._results_list.setVisible(bool(matches))
        if matches:
            self._results_list.setCurrentRow(0)

    def clear(self) -> None:
        """Clear the text field and close the dropdown."""
        self._line_edit.clear()
        self.set_matches([])

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        row = self._results_list.row(item)
        if 0 <= row < len(self._matches):
            self.match_chosen.emit(self._matches[row])

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._line_edit and event.type() == QEvent.Type.KeyPress:
            key_event = event
            assert isinstance(key_event, QKeyEvent)
            if key_event.key() == Qt.Key.Key_Down:
                self._move_selection(1)
                return True
            if key_event.key() == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current = self._results_list.currentItem()
                if current is not None:
                    self._on_item_activated(current)
                    return True
            if key_event.key() == Qt.Key.Key_Escape:
                self._results_list.setVisible(False)
                return True
        return super().eventFilter(watched, event)

    def _move_selection(self, delta: int) -> None:
        if not self._matches:
            return
        current = self._results_list.currentRow()
        new_row = max(0, min(len(self._matches) - 1, current + delta))
        self._results_list.setCurrentRow(new_row)
        self._results_list.setVisible(True)
