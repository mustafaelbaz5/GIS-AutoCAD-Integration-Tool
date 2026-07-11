"""Output path picker widget, per project brief §7.3."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from src.infrastructure.config.app_settings import load_last_output_dir, save_last_output_dir
from src.presentation.i18n.ar import CHANGE_BUTTON, CHOOSE_FOLDER_TITLE, OUTPUT_LABEL

DEFAULT_OUTPUT_DIR = Path.home() / "Desktop" / "GIS_Output"


class PathSelector(QWidget):
    """Shows the current output folder and lets the user change it.

    Defaults to `~/Desktop/GIS_Output/` on first run, auto-created if
    missing, per project brief §7.3. On later runs, defaults to the
    last-used folder instead — persisted per Iteration 2 §8.3.
    """

    path_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = load_last_output_dir() or DEFAULT_OUTPUT_DIR
        self._path.mkdir(parents=True, exist_ok=True)

        self._path_label = QLabel(str(self._path))
        change_button = QPushButton(CHANGE_BUTTON)
        change_button.clicked.connect(self._on_change_clicked)

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(OUTPUT_LABEL))
        layout.addWidget(self._path_label, stretch=1)
        layout.addWidget(change_button)

    @property
    def path(self) -> Path:
        """The currently selected output directory."""
        return self._path

    def _on_change_clicked(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, CHOOSE_FOLDER_TITLE, str(self._path))
        if not chosen:
            return
        self._path = Path(chosen)
        self._path.mkdir(parents=True, exist_ok=True)
        self._path_label.setText(str(self._path))
        save_last_output_dir(self._path)
        self.path_changed.emit(str(self._path))
