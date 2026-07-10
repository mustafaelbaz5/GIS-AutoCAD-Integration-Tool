"""The four cardinal borders of a land parcel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Borders:
    """A parcel's four cardinal neighbor descriptions.

    Each field holds either a fixed landmark string (e.g. "مصرف صرف") or
    a neighboring holder's name, as written in the source file. Values are
    the raw border text used by the spatial sorter to chain parcels
    together, per the East→West / North-South algorithm in the brief.
    """

    east: str | None
    """الحد الشرقى"""

    south: str | None
    """الحد القبلى"""

    west: str | None
    """الحد الغربى"""

    north: str | None
    """الحد البحرى"""
