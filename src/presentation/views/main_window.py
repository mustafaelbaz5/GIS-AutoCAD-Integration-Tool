"""Main application window shell (Phase 6 foundation).

Widgets (drop zones, progress panel, log console) are added in later
phases; this establishes the window, RTL layout direction, and title.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from src.presentation.i18n.ar import APP_TITLE


class MainWindow(QMainWindow):
    """The application's main window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(900, 650)
        self.setCentralWidget(self._build_central_widget())

    def _build_central_widget(self) -> QWidget:
        central = QWidget()
        layout = QVBoxLayout(central)

        title_label = QLabel(APP_TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return central
