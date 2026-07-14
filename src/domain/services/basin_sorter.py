"""Basin sorter service.

Replaces the earlier neighbor-chaining spatial sorter: parcels within
each basin are simply ordered alphabetically (A→Z) by the holder's
name (اسم الحائز), per the user's explicit request to drop the
border-text-chaining approach entirely. Basins themselves keep their
first-appearance order from the input.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from src.domain.entities.parcel import Parcel
from src.shared.arabic_normalizer import normalize_arabic


@dataclass(frozen=True)
class BasinSortResult:
    """Outcome of basin sorting: ordered parcels, per the module docstring."""

    parcels: list[Parcel]


class BasinSorter:
    """Orders parcels within each basin alphabetically by holder name."""

    def sort(self, parcels: Sequence[Parcel]) -> BasinSortResult:
        """Group parcels by basin, then sort each basin's parcels A→Z.

        Args:
            parcels: All parcels to sort, from any/all basins.

        Returns:
            Parcels ordered basin-by-basin (basins in first-appearance
            order), each basin's parcels alphabetical by holder name.
        """
        basins: dict[str, list[Parcel]] = {}
        for parcel in parcels:
            key = normalize_arabic(parcel.basin.name or "")
            basins.setdefault(key, []).append(parcel)

        ordered: list[Parcel] = []
        for basin_parcels in basins.values():
            basin_parcels.sort(key=lambda p: normalize_arabic(p.holder.name or ""))
            ordered.extend(basin_parcels)

        return BasinSortResult(parcels=ordered)
