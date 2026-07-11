"""Excel output formatting constants, per Iteration 2 Task B.

Centralized here (not hard-coded in the writer) so a single-file
change tweaks the output's typography and column sizing.
"""

from dataclasses import dataclass, field

from src.shared.font_availability import has_bundled_font

_NARROW_COLUMNS: frozenset[str] = frozenset({"فدان", "قيراط", "سهم", "رقم الحيازة"})
_COLUMN_WIDTH_OVERRIDES: dict[str, int] = {"الرقم القومي": 20, "رقم الأرض": 16}


def _resolve_font_family() -> str:
    return "Cairo" if has_bundled_font("cairo") else "Calibri"


@dataclass(frozen=True)
class FormattingConfig:
    """Tunable Excel output formatting values.

    Args:
        max_column_width: Upper bound on any column's width, in
            characters. Excel shows the full value on hover / in the
            cell-reference bar even when the displayed cell truncates.
        min_column_width: Lower bound, so headers stay readable even
            for columns with very short content.
        narrow_column_width: Upper bound applied instead of
            `max_column_width` for `narrow_columns` (short, fixed-format
            fields that never need much horizontal space).
        narrow_columns: Output column headers that use
            `narrow_column_width` instead of `max_column_width`.
        column_width_overrides: Explicit fixed widths for specific
            columns, taking priority over both the narrow and default
            sizing rules — for columns that need a deliberately larger
            width regardless of content length (e.g. الرقم القومي).
        body_font_size: Point size for data rows and the totals row.
        header_font_size: Point size for the header row.
        font_family: "Cairo" if a Cairo font file is bundled in
            `resources/fonts/` on this machine, else "Calibri" — resolved
            once at import time.
        header_row_height: Row height (points) for the header row.
        data_row_height: Row height (points) for data and totals rows.
    """

    max_column_width: int = 35
    min_column_width: int = 8
    narrow_column_width: int = 12
    narrow_columns: frozenset[str] = field(default_factory=lambda: _NARROW_COLUMNS)
    column_width_overrides: dict[str, int] = field(
        default_factory=lambda: dict(_COLUMN_WIDTH_OVERRIDES)
    )
    body_font_size: int = 13
    header_font_size: int = 14
    font_family: str = field(default_factory=_resolve_font_family)
    header_row_height: float = 22.0
    data_row_height: float = 18.0

    def column_width(self, header: str, max_content_length: int) -> int:
        """Compute a column's width from its header and longest content."""
        if header in self.column_width_overrides:
            return self.column_width_overrides[header]
        cap = self.narrow_column_width if header in self.narrow_columns else self.max_column_width
        return max(min(max_content_length + 2, cap), self.min_column_width)


DEFAULT_FORMATTING_CONFIG = FormattingConfig()
