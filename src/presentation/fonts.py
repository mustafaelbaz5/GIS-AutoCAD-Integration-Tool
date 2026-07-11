"""Arabic font loading, per project brief §7.1.

Loads a bundled Cairo/Tajawal font from `resources/fonts/` if present,
and falls back to a system font known to render Arabic well. The
`resources/fonts/` directory ships empty in this repository — an
operator must drop the actual Cairo or Tajawal `.ttf`/`.otf` files
there (e.g. from Google Fonts) before packaging, since font files
cannot be fetched as part of this build.
"""

from PySide6.QtGui import QFontDatabase

from src.shared.paths import get_app_root

_FALLBACK_FAMILY = "Segoe UI"


def load_app_font_family() -> str:
    """Load bundled fonts, if any, and return the family name to use.

    Returns:
        The bundled font's family name if a font file was found and
        loaded successfully, otherwise a system fallback family with
        reasonable Arabic glyph support.
    """
    fonts_dir = get_app_root() / "resources" / "fonts"
    if not fonts_dir.is_dir():
        return _FALLBACK_FAMILY

    for font_path in sorted(fonts_dir.glob("*.ttf")) + sorted(fonts_dir.glob("*.otf")):
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id == -1:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]

    return _FALLBACK_FAMILY
