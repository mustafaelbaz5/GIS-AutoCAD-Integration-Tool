"""Spatial sorter service, per project brief §5.5."""

from collections.abc import Sequence
from dataclasses import dataclass

from src.domain.entities.parcel import Parcel
from src.shared.arabic_normalizer import normalize_arabic
from src.shared.fuzzy_matcher import best_match

DEFAULT_MATCH_THRESHOLD = 85.0


@dataclass(frozen=True)
class SpatialSortResult:
    """Outcome of spatial sorting: ordered parcels plus any warnings."""

    parcels: list[Parcel]
    warnings: list[str]


class SpatialSorter:
    """Orders parcels within each basin East→West, row by row, per §5.5.

    Domain services stay free of infrastructure concerns (no logging), so
    issues encountered while chaining parcels together are collected as
    warning strings in the result rather than logged directly; the
    application layer decides how to surface them.
    """

    def __init__(
        self,
        landmark_keywords: Sequence[str],
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
    ) -> None:
        self._landmark_keywords = [normalize_arabic(k) for k in landmark_keywords]
        self._match_threshold = match_threshold

    def sort(self, parcels: Sequence[Parcel]) -> SpatialSortResult:
        """Group parcels by basin and order each basin's parcels.

        Args:
            parcels: All parcels to sort, from any/all basins.

        Returns:
            Parcels ordered basin-by-basin, plus any warnings raised
            while chaining parcels together. No parcel is ever dropped.
        """
        warnings: list[str] = []
        ordered: list[Parcel] = []

        for basin_name, basin_parcels in self._group_by_basin(parcels).items():
            basin_result = self._sort_basin(basin_parcels, basin_name)
            ordered.extend(basin_result.parcels)
            warnings.extend(basin_result.warnings)

        return SpatialSortResult(parcels=ordered, warnings=warnings)

    def _group_by_basin(self, parcels: Sequence[Parcel]) -> dict[str, list[Parcel]]:
        groups: dict[str, list[Parcel]] = {}
        for parcel in parcels:
            key = normalize_arabic(parcel.basin.name or "")
            groups.setdefault(key, []).append(parcel)
        return groups

    def _sort_basin(self, parcels: list[Parcel], basin_name: str) -> SpatialSortResult:
        remaining = list(parcels)
        ordered: list[Parcel] = []
        warnings: list[str] = []

        start = self._find_starting_parcel(remaining)
        if start is None and remaining:
            start = remaining[0]
            warnings.append(
                f"[{basin_name}] No starting parcel with a landmark eastern "
                f"border found; starting arbitrarily with holding "
                f"{start.holding_id}."
            )

        while start is not None:
            row, row_warnings = self._build_row(start, remaining)
            ordered.extend(row)
            warnings.extend(row_warnings)
            for placed in row:
                remaining.remove(placed)

            start = self._find_next_row_start(row[0], remaining)

        if remaining:
            warnings.append(
                f"[{basin_name}] {len(remaining)} parcel(s) could not be "
                f"placed in sequence; appended at the end of the basin block."
            )
            ordered.extend(remaining)

        return SpatialSortResult(parcels=ordered, warnings=warnings)

    def _find_starting_parcel(self, parcels: list[Parcel]) -> Parcel | None:
        for parcel in parcels:
            if self._is_landmark(parcel.borders.east):
                return parcel
        return None

    def _build_row(self, start: Parcel, pool: list[Parcel]) -> tuple[list[Parcel], list[str]]:
        row = [start]
        warnings: list[str] = []
        current = start
        used_ids = {id(start)}

        while True:
            west = current.borders.west
            if self._is_landmark(west):
                break
            if west is None or not west.strip():
                break

            candidates = [p for p in pool if id(p) not in used_ids]
            neighbor = self._find_holder_match(west, candidates)
            if neighbor is None:
                warnings.append(
                    f"No western neighbor found for holding "
                    f"{current.holding_id} (border text: '{west}')."
                )
                break

            row.append(neighbor)
            used_ids.add(id(neighbor))
            current = neighbor

        return row, warnings

    def _find_next_row_start(self, row_first_parcel: Parcel, pool: list[Parcel]) -> Parcel | None:
        for border_text in (row_first_parcel.borders.north, row_first_parcel.borders.south):
            if border_text is None or not border_text.strip():
                continue
            neighbor = self._find_holder_match(border_text, pool)
            if neighbor is not None:
                return neighbor
        return None

    def _find_holder_match(self, border_text: str, candidates: list[Parcel]) -> Parcel | None:
        names_to_parcel: dict[str, Parcel] = {}
        for candidate in candidates:
            if candidate.holder.name:
                names_to_parcel[normalize_arabic(candidate.holder.name)] = candidate

        if not names_to_parcel:
            return None
        matched_name = best_match(
            normalize_arabic(border_text), names_to_parcel.keys(), self._match_threshold
        )
        return names_to_parcel.get(matched_name) if matched_name else None

    def _is_landmark(self, border_text: str | None) -> bool:
        if not border_text or not border_text.strip():
            return False
        normalized = normalize_arabic(border_text)
        return any(keyword in normalized for keyword in self._landmark_keywords)
