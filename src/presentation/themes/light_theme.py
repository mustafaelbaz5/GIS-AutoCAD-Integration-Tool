"""Light theme palette and stylesheet — togglable alternative to dark mode."""

from src.presentation.themes.dark_theme import Palette, build_stylesheet

LIGHT_PALETTE = Palette(
    background="#f8fafc",
    surface="#ffffff",
    primary_accent="#3b82f6",
    success_accent="#22c55e",
    text_primary="#0f172a",
    text_secondary="#475569",
)

LIGHT_STYLESHEET = build_stylesheet(LIGHT_PALETTE)
