"""Search window for finding and inspecting individual holdings.

Opened as a separate, non-modal top-level window from MainWindow's
"🔍 بحث في الحيازات" button or the أدوات → بحث menu item, per
Iteration 2 Task C §6.2.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.domain.entities.parcel import Parcel
from src.presentation.i18n.ar import (
    BACK_TO_RESULTS_BUTTON,
    CHOOSE_PARCEL_TITLE,
    COPY_DATA_BUTTON,
    EMPTY_VALUE_PLACEHOLDER,
    FIELD_HOLDER_NAME,
    FIELD_HOLDING_ID,
    FIELD_LAND_NUMBER,
    FIELD_NATIONAL_ID,
    NO_OUTPUT_FILE_MESSAGE,
    OPEN_DIFFERENT_FILE_BUTTON,
    SEARCH_WINDOW_TITLE,
)
from src.presentation.viewmodels.search_viewmodel import SearchViewModel
from src.presentation.widgets.border_compass import BorderCompass
from src.presentation.widgets.holding_detail_panel import HoldingDetailPanel
from src.presentation.widgets.search_input import SearchInput


class SearchWindow(QMainWindow):
    """Standalone window: search a loaded output file and inspect a holding."""

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self._viewmodel = SearchViewModel()
        self._current_parcel: Parcel | None = None

        self.setWindowTitle(SEARCH_WINDOW_TITLE)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(700, 800)
        self.setCentralWidget(self._build_central_widget())
        self._connect_viewmodel()
        self._set_detail_visible(False)

        if initial_file is not None:
            self._viewmodel.load_file(initial_file)
        else:
            self._empty_state_label.setText(NO_OUTPUT_FILE_MESSAGE)

    def _build_central_widget(self) -> QWidget:
        central = QWidget()
        layout = QVBoxLayout(central)

        self._empty_state_label = QLabel(NO_OUTPUT_FILE_MESSAGE)
        self._empty_state_label.setWordWrap(True)
        layout.addWidget(self._empty_state_label)

        self._search_input = SearchInput()
        layout.addWidget(self._search_input)

        self._detail_panel = HoldingDetailPanel()
        layout.addWidget(self._detail_panel)

        self._border_compass = BorderCompass()
        layout.addWidget(self._border_compass)

        actions_row = QHBoxLayout()
        self._copy_button = QPushButton(COPY_DATA_BUTTON)
        self._copy_button.clicked.connect(self._on_copy_clicked)
        self._open_file_button = QPushButton(OPEN_DIFFERENT_FILE_BUTTON)
        self._open_file_button.clicked.connect(self._on_open_file_clicked)
        self._back_button = QPushButton(BACK_TO_RESULTS_BUTTON)
        self._back_button.clicked.connect(self._on_back_clicked)
        actions_row.addWidget(self._copy_button)
        actions_row.addWidget(self._open_file_button)
        actions_row.addWidget(self._back_button)
        layout.addLayout(actions_row)

        return central

    def _connect_viewmodel(self) -> None:
        self._search_input.text_changed.connect(self._viewmodel.search)
        self._search_input.match_chosen.connect(self._viewmodel.select_match)
        self._border_compass.neighbor_clicked.connect(self._viewmodel.navigate_to_neighbor)

        self._viewmodel.matches_changed.connect(self._search_input.set_matches)
        self._viewmodel.parcel_selected.connect(self._on_parcel_selected)
        self._viewmodel.parcels_available.connect(self._on_parcels_available)
        self._viewmodel.load_error.connect(self._on_load_error)
        self._viewmodel.file_loaded.connect(self._on_file_loaded)

    def _on_parcel_selected(self, parcel: Parcel) -> None:
        self._current_parcel = parcel
        self._detail_panel.display(parcel)
        self._border_compass.display(parcel.borders, str(parcel.holding_id))
        self._set_detail_visible(True)

    def _on_parcels_available(self, parcels: list[Parcel]) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(CHOOSE_PARCEL_TITLE)
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for parcel in parcels:
            label = f"{FIELD_LAND_NUMBER}: {parcel.land_number or EMPTY_VALUE_PLACEHOLDER}"
            list_widget.addItem(label)
        layout.addWidget(list_widget)

        def choose(item: QListWidgetItem) -> None:
            row = list_widget.row(item)
            dialog.accept()
            self._viewmodel.select_parcel(parcels[row])

        list_widget.itemActivated.connect(choose)
        list_widget.itemClicked.connect(choose)
        dialog.resize(300, 400)
        dialog.exec()

    def _on_load_error(self, message: str) -> None:
        self._empty_state_label.setText(message)
        self._empty_state_label.setVisible(True)
        self._set_detail_visible(False)

    def _on_file_loaded(self, path: str, row_count: int) -> None:
        self._empty_state_label.setVisible(False)

    def _on_copy_clicked(self) -> None:
        if self._current_parcel is None:
            return
        text = self._format_parcel_for_clipboard(self._current_parcel)
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def _on_open_file_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, filter="Excel Files (*.xlsx)")
        if path:
            self._viewmodel.load_file(Path(path))

    def _on_back_clicked(self) -> None:
        self._set_detail_visible(False)
        self._search_input.clear()

    def _set_detail_visible(self, visible: bool) -> None:
        self._detail_panel.setVisible(visible)
        self._border_compass.setVisible(visible)
        self._copy_button.setVisible(visible)
        self._back_button.setVisible(visible)

    def _format_parcel_for_clipboard(self, parcel: Parcel) -> str:
        lines = [
            f"{FIELD_HOLDER_NAME}: {parcel.holder.name or EMPTY_VALUE_PLACEHOLDER}",
            f"{FIELD_NATIONAL_ID}: {parcel.holder.national_id or EMPTY_VALUE_PLACEHOLDER}",
            f"{FIELD_HOLDING_ID}: {parcel.holding_id}",
            f"{FIELD_LAND_NUMBER}: {parcel.land_number or EMPTY_VALUE_PLACEHOLDER}",
        ]
        return "\n".join(lines)
