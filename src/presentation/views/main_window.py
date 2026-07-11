"""Main application window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from src.presentation.i18n.ar import (
    APP_TITLE,
    BASE_FILE_TITLE,
    LOG_PANEL_TITLE,
    SECONDARY_FILE_TITLE,
    START_BUTTON,
)
from src.presentation.viewmodels.main_viewmodel import MainViewModel
from src.presentation.widgets.drop_zone import DropZone
from src.presentation.widgets.log_console import LogConsole, LogLevel
from src.presentation.widgets.path_selector import PathSelector
from src.presentation.widgets.progress_panel import ProgressPanel


class MainWindow(QMainWindow):
    """The application's main window: wires widgets to the view-model."""

    def __init__(self) -> None:
        super().__init__()
        self._viewmodel = MainViewModel()

        self.setWindowTitle(APP_TITLE)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(900, 700)
        self.setCentralWidget(self._build_central_widget())
        self._connect_viewmodel()

    def _build_central_widget(self) -> QWidget:
        central = QWidget()
        layout = QVBoxLayout(central)

        title_label = QLabel(APP_TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        drop_zones_row = QHBoxLayout()
        self._base_drop_zone = DropZone(BASE_FILE_TITLE)
        self._secondary_drop_zone = DropZone(SECONDARY_FILE_TITLE)
        drop_zones_row.addWidget(self._base_drop_zone)
        drop_zones_row.addWidget(self._secondary_drop_zone)
        layout.addLayout(drop_zones_row)

        self._path_selector = PathSelector()
        layout.addWidget(self._path_selector)

        self._start_button = QPushButton(START_BUTTON)
        self._start_button.setProperty("success", True)
        self._start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self._start_button)

        self._progress_panel = ProgressPanel()
        layout.addWidget(self._progress_panel)

        layout.addWidget(QLabel(LOG_PANEL_TITLE))
        self._log_console = LogConsole()
        layout.addWidget(self._log_console, stretch=1)

        return central

    def _connect_viewmodel(self) -> None:
        self._base_drop_zone.file_selected.connect(self._viewmodel.set_base_file)
        self._secondary_drop_zone.file_selected.connect(self._viewmodel.set_secondary_file)
        self._path_selector.path_changed.connect(self._viewmodel.set_output_dir)

        self._viewmodel.progress_changed.connect(self._progress_panel.set_progress)
        self._viewmodel.log_emitted.connect(self._on_log_emitted)

    def _on_start_clicked(self) -> None:
        self._log_console.clear_log()
        self._progress_panel.reset()
        self._viewmodel.run_pipeline()

    def _on_log_emitted(self, message: str, level: str) -> None:
        self._log_console.log(message, LogLevel(level))
