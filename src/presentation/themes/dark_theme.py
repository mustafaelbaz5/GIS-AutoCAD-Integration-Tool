"""Dark theme palette and stylesheet, per project brief §7.1."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    """A named set of colors used to build a Qt stylesheet."""

    background: str
    surface: str
    primary_accent: str
    success_accent: str
    text_primary: str
    text_secondary: str


DARK_PALETTE = Palette(
    background="#0f172a",
    surface="#1e293b",
    primary_accent="#3b82f6",
    success_accent="#22c55e",
    text_primary="#f1f5f9",
    text_secondary="#94a3b8",
)


def build_stylesheet(palette: Palette) -> str:
    """Build a Qt stylesheet (QSS) from a color palette.

    Shared between the dark and light themes so both stay structurally
    identical and only the color values differ.
    """
    return f"""
    QMainWindow, QWidget {{
        background-color: {palette.background};
        color: {palette.text_primary};
        font-size: 14px;
    }}
    QLabel {{
        color: {palette.text_primary};
    }}
    QLabel[secondary="true"] {{
        color: {palette.text_secondary};
    }}
    QPushButton {{
        background-color: {palette.primary_accent};
        color: {palette.text_primary};
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
    }}
    QPushButton:hover {{
        background-color: {palette.surface};
    }}
    QPushButton[success="true"] {{
        background-color: {palette.success_accent};
    }}
    QFrame[card="true"] {{
        background-color: {palette.surface};
        border-radius: 12px;
    }}
    QProgressBar {{
        background-color: {palette.surface};
        border-radius: 6px;
        text-align: center;
        color: {palette.text_primary};
    }}
    QProgressBar::chunk {{
        background-color: {palette.primary_accent};
        border-radius: 6px;
    }}
    """


DARK_STYLESHEET = build_stylesheet(DARK_PALETTE)
