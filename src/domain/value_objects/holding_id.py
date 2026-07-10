"""Holding ID value object (رقم الحيازة)."""

from dataclasses import dataclass

from src.domain.exceptions import InvalidHoldingIdError


@dataclass(frozen=True)
class HoldingId:
    """A validated holding ID, preserving its original display form.

    Leading zeros (e.g. "010") are meaningful for display and are kept
    as-is here. Use :func:`normalize_for_join` when comparing two holding
    IDs from different sources, per the join-key rule in the project brief.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidHoldingIdError("Holding ID must not be empty")

    def __str__(self) -> str:
        return self.value


def normalize_for_join(raw_value: str) -> str:
    """Normalize a holding ID for cross-source comparison.

    Strips whitespace and leading zeros so that "010" and "10" from two
    different files are recognized as the same holding, per the join-key
    rule (base file `رقم الحيازة` vs. secondary file `رقم حيازه 2022`).
    A value of only zeros collapses to a single "0" rather than an empty
    string.
    """
    stripped = str(raw_value).strip()
    without_leading_zeros = stripped.lstrip("0")
    return without_leading_zeros or "0"
