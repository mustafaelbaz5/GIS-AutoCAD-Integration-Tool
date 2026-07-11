"""Color-coded operation log console, per project brief §7.3."""

from enum import Enum

from PySide6.QtWidgets import QTextEdit, QWidget


class LogLevel(Enum):
    """Severity of a log line, each rendered with its own icon/color."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


_ICONS = {LogLevel.SUCCESS: "✔", LogLevel.WARNING: "⚠", LogLevel.ERROR: "✖"}
_COLORS = {LogLevel.SUCCESS: "#22c55e", LogLevel.WARNING: "#f59e0b", LogLevel.ERROR: "#ef4444"}


class LogConsole(QTextEdit):
    """A read-only, color-coded operation log (✔ green, ⚠ amber, ✖ red)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)

    def log(self, message: str, level: LogLevel) -> None:
        """Append a color-coded, icon-prefixed line."""
        icon = _ICONS[level]
        color = _COLORS[level]
        self.append(f'<span style="color:{color};">{icon} {message}</span>')

    def success(self, message: str) -> None:
        self.log(message, LogLevel.SUCCESS)

    def warning(self, message: str) -> None:
        self.log(message, LogLevel.WARNING)

    def error(self, message: str) -> None:
        self.log(message, LogLevel.ERROR)

    def clear_log(self) -> None:
        """Clear all log lines."""
        self.clear()
