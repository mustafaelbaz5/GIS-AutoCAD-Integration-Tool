"""Application entry point."""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.presentation.fonts import load_app_font_family
from src.presentation.themes.dark_theme import DARK_STYLESHEET
from src.presentation.views.main_window import MainWindow


def main() -> None:
    """Launch the application window."""
    app = QApplication(sys.argv)
    app.setFont(QFont(load_app_font_family()))
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
