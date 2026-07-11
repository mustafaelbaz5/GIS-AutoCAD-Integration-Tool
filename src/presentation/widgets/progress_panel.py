"""Progress bar with descriptive status text, per project brief §7.3."""

from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class ProgressPanel(QWidget):
    """Displays a progress bar plus a description of the current step."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._status_label = QLabel("")
        self._status_label.setProperty("secondary", True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._bar)
        layout.addWidget(self._status_label)

    def set_progress(self, percent: int, message: str) -> None:
        """Update the bar's value and the status text beneath it."""
        self._bar.setValue(max(0, min(100, percent)))
        self._status_label.setText(message)

    def reset(self) -> None:
        """Reset the panel to its initial (0%, no message) state."""
        self.set_progress(0, "")
