"""Cell-value parsing helpers shared by the Excel readers.

Excel-specific cleanup (placeholder punctuation, mixed numeric/text
cells) belongs here rather than in `shared/`, since it is not a general
Arabic-text concern but an artifact of how these particular source
files are authored.
"""

_BORDER_PLACEHOLDERS = {"،،", "،", "-", "--", "_", "__"}


def clean_text(value: object) -> str | None:
    """Return a stripped string, or None if the cell is empty."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_border(value: object) -> str | None:
    """Like `clean_text`, but also treats placeholder punctuation as empty.

    Source files use "،،", "-", or "_" to mark a border cell with no
    real value. These are not landmark or holder-name text and would
    otherwise confuse the spatial sorter.
    """
    text = clean_text(value)
    if text is None or text in _BORDER_PLACEHOLDERS:
        return None
    return text


def parse_number(value: object) -> float | None:
    """Parse an area-component cell (فدان/قيراط/سهم), tolerating strings,
    ints, floats, and blanks.

    Source files occasionally contain a negative value here (a data
    error in the source report, not a real physical measurement —
    confirmed against real rows that are otherwise normal holdings).
    Since area can never legitimately be negative, these are clamped
    to 0 rather than propagated or fabricated into something else.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return max(0.0, float(value))
    text = str(value).strip()
    if text == "":
        return None
    try:
        return max(0.0, float(text))
    except ValueError:
        return None


def normalize_national_id(value: object) -> str | None:
    """Normalize a national ID cell to a zero-padded 14-digit string.

    Egyptian national IDs are a fixed-width 14 digits; some source rows
    store the value as a number, which silently drops leading zeros.
    Re-padding to 14 digits restores the correct format without
    inventing any digit.
    """
    text = clean_text(value)
    if text is None:
        return None
    if text.isdigit():
        return text.zfill(14)
    return text
