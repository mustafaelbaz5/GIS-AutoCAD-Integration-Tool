"""Checks whether a bundled font file is available.

Shared by the GUI's font loading (`presentation/fonts.py`) and the
Excel writer's font-family selection, so infrastructure code can make
this check without depending on the presentation layer.
"""

from src.shared.paths import get_app_root


def has_bundled_font(family_hint: str) -> bool:
    """True if a `.ttf`/`.otf` file matching `family_hint` is bundled.

    Args:
        family_hint: Case-insensitive substring to match against font
            file stems (e.g. "cairo").
    """
    fonts_dir = get_app_root() / "resources" / "fonts"
    if not fonts_dir.is_dir():
        return False

    hint = family_hint.lower()
    for pattern in ("*.ttf", "*.otf"):
        for font_path in fonts_dir.glob(pattern):
            if hint in font_path.stem.lower():
                return True
    return False
