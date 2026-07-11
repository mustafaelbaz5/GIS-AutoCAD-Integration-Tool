"""Main application window."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.i18n.ar import (
    APP_TITLE,
    BASE_FILE_TITLE,
    CANCEL_BUTTON,
    CLOSE_BUTTON,
    LOG_PANEL_TITLE,
    OPEN_FILE_BUTTON,
    OPEN_FOLDER_BUTTON,
    SECONDARY_FILE_TITLE,
    START_BUTTON,
    SUCCESS_DIALOG_MESSAGE,
    SUCCESS_DIALOG_TITLE,
)
from src.presentation.viewmodels.main_viewmodel import MainViewModel
from src.presentation.widgets.drop_zone import DropZone
from src.presentation.widgets.log_console import LogConsole, LogLevel
from src.presentation.widgets.path_selector import PathSelector
from src.presentation.widgets.progress_panel import ProgressPanel
from src.presentation.workers.pipeline_worker import PipelineWorker


class MainWindow(QMainWindow):
    """The application's main window: wires widgets to the view-model.

    The "Start" button runs the pipeline on a background `QThread` via
    `PipelineWorker`, so the window stays responsive; "Cancel" requests
    cooperative cancellation and the thread is always cleanly quit and
    torn down in `_on_pipeline_finished`, whether the run succeeded,
    failed, or was cancelled.
    """

    def __init__(self) -> None:
        super().__init__()
        self._viewmodel = MainViewModel()
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

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

        buttons_row = QHBoxLayout()
        self._start_button = QPushButton(START_BUTTON)
        self._start_button.setProperty("success", True)
        self._start_button.clicked.connect(self._on_start_clicked)
        self._cancel_button = QPushButton(CANCEL_BUTTON)
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        buttons_row.addWidget(self._start_button)
        buttons_row.addWidget(self._cancel_button)
        layout.addLayout(buttons_row)

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
        self._start_button.setEnabled(False)
        self._cancel_button.setEnabled(True)
        self._viewmodel.reset_cancel_flag()

        self._thread = QThread()
        self._worker = PipelineWorker(self._viewmodel)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._viewmodel.finished.connect(self._on_pipeline_finished)
        self._thread.start()

    def _on_cancel_clicked(self) -> None:
        self._viewmodel.request_cancel()
        self._cancel_button.setEnabled(False)

    def _on_log_emitted(self, message: str, level: str) -> None:
        self._log_console.log(message, LogLevel(level))

    def _on_pipeline_finished(self, success: bool, output_path: str) -> None:
        self._viewmodel.finished.disconnect(self._on_pipeline_finished)
        self._teardown_thread()

        self._start_button.setEnabled(True)
        self._cancel_button.setEnabled(False)

        if success:
            self._show_success_dialog(output_path)

    def _teardown_thread(self) -> None:
        if self._thread is None:
            return
        self._thread.quit()
        self._thread.wait()
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        self._thread.deleteLater()
        self._thread = None

    def _show_success_dialog(self, output_path: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(SUCCESS_DIALOG_TITLE)
        box.setText(SUCCESS_DIALOG_MESSAGE)
        open_folder_button = box.addButton(OPEN_FOLDER_BUTTON, QMessageBox.ButtonRole.ActionRole)
        open_file_button = box.addButton(OPEN_FILE_BUTTON, QMessageBox.ButtonRole.ActionRole)
        box.addButton(CLOSE_BUTTON, QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        path = Path(output_path)
        if clicked is open_folder_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
        elif clicked is open_file_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
