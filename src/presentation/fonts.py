"""Arabic font loading, per project brief §7.1.

Loads a bundled Cairo/Tajawal font from `resources/fonts/` if present,
and falls back to a system font known to render Arabic well. The
`resources/fonts/` directory ships empty in this repository — an
operator must drop the actual Cairo or Tajawal `.ttf`/`.otf` files
there (e.g. from Google Fonts) before packaging, since font files
cannot be fetched as part of this build.
"""

from pathlib import Path

from PySide6.QtGui import QFontDatabase

_FONTS_DIR = Path(__file__).resolve().parents[2] / "resources" / "fonts"
_FALLBACK_FAMILY = "Segoe UI"


def load_app_font_family() -> str:
    """Load bundled fonts, if any, and return the family name to use.

    Returns:
        The bundled font's family name if a font file was found and
        loaded successfully, otherwise a system fallback family with
        reasonable Arabic glyph support.
    """
    if not _FONTS_DIR.is_dir():
        return _FALLBACK_FAMILY

    for font_path in sorted(_FONTS_DIR.glob("*.ttf")) + sorted(_FONTS_DIR.glob("*.otf")):
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]

    return _FALLBACK_FAMILY
