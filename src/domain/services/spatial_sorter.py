"""Spatial sorter service, per project brief §5.5.

Corrected per the boustrophedon ("as the ox turns") spec: parcels within
a basin are traced as a single continuous zigzag chain — the first row
runs East→West, then each subsequent row starts from a vertical neighbor
(القبلي/south tried first, then البحري/north) of the *last* parcel in
the previous row and runs in the opposite horizontal direction,
alternating every row. This replaced an earlier (incorrect) version that
always restarted each row from a fresh eastern-landmark search and always
read the western border, never alternating direction.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto

from src.domain.entities.parcel import Parcel
from src.shared.arabic_normalizer import normalize_arabic
from src.shared.fuzzy_matcher import best_match

DEFAULT_MATCH_THRESHOLD = 85.0


class _RowDirection(Enum):
    EAST_TO_WEST = auto()
    WEST_TO_EAST = auto()

    def opposite(self) -> "_RowDirection":
        if self is _RowDirection.EAST_TO_WEST:
            return _RowDirection.WEST_TO_EAST
        return _RowDirection.EAST_TO_WEST


@dataclass(frozen=True)
class SpatialSortResult:
    """Outcome of spatial sorting: ordered parcels plus any warnings.

    Args:
        parcels: The ordered parcels.
        warnings: Human-readable warnings raised while chaining parcels.
        unplaced_count: How many times a row ended with no vertical
            neighbor match, forcing the chain to resume from an
            arbitrary remaining parcel instead — a structured count for
            reporting (e.g. a statistics panel), distinct from the
            free-text `warnings`.
    """

    parcels: list[Parcel]
    warnings: list[str]
    unplaced_count: int = 0


class SpatialSorter:
    """Orders parcels within each basin in a boustrophedon (snake) pattern.

    Each basin is traced as one continuous zigzag: the first row runs
    East→West from a landmark-anchored starting parcel; each following
    row starts from a vertical neighbor of the previous row's *last*
    parcel and runs in the opposite horizontal direction. Domain
    services stay free of infrastructure concerns (no logging), so
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
        unplaced_count = 0

        for basin_name, basin_parcels in self._group_by_basin(parcels).items():
            basin_result = self._sort_basin(basin_parcels, basin_name)
            ordered.extend(basin_result.parcels)
            warnings.extend(basin_result.warnings)
            unplaced_count += basin_result.unplaced_count

        return SpatialSortResult(parcels=ordered, warnings=warnings, unplaced_count=unplaced_count)

    def _group_by_basin(self, parcels: Sequence[Parcel]) -> dict[str, list[Parcel]]:
        groups: dict[str, list[Parcel]] = {}
        for parcel in parcels:
            key = normalize_arabic(parcel.basin.name or "")
            groups.setdefault(key, []).append(parcel)
        return groups

    def _sort_basin(self, parcels: list[Parcel], basin_name: str) -> SpatialSortResult:
        pool = list(parcels)
        if not pool:
            return SpatialSortResult(parcels=[], warnings=[])

        visited: set[int] = set()
        ordered: list[Parcel] = []
        warnings: list[str] = []
        unplaced_count = 0

        current: Parcel | None = self._find_starting_parcel(pool)
        if current is None:
            current = pool[0]
            warnings.append(
                f"[{basin_name}] No starting parcel with a landmark eastern "
                f"border found; starting arbitrarily with holding "
                f"{current.holding_id}."
            )

        direction = _RowDirection.EAST_TO_WEST

        while current is not None:
            row, row_warnings = self._trace_horizontal_chain(current, direction, visited, pool)
            ordered.extend(row)
            warnings.extend(row_warnings)

            if len(visited) >= len(pool):
                break

            last_in_row = row[-1]
            next_parcel = self._find_vertical_neighbor(last_in_row, pool, visited)

            if next_parcel is None:
                next_parcel = self._first_unvisited(pool, visited)
                if next_parcel is not None:
                    unplaced_count += 1
                    warnings.append(
                        f"[{basin_name}] No vertical neighbor found for holding "
                        f"{last_in_row.holding_id}; resumed from an arbitrary "
                        f"remaining parcel (holding {next_parcel.holding_id})."
                    )

            direction = direction.opposite()
            current = next_parcel

        leftovers = [p for p in pool if id(p) not in visited]
        if leftovers:
            # Defensive safety net only — the arbitrary-resume fallback
            # above already sweeps in every remaining parcel, so this
            # should never actually fire, but no parcel may ever be
            # dropped even in an unforeseen edge case.
            warnings.append(
                f"[{basin_name}] {len(leftovers)} parcel(s) could not be "
                f"placed in sequence; appended at the end of the basin block."
            )
            ordered.extend(leftovers)
            unplaced_count += len(leftovers)

        return SpatialSortResult(parcels=ordered, warnings=warnings, unplaced_count=unplaced_count)

    def _trace_horizontal_chain(
        self, start: Parcel, direction: _RowDirection, visited: set[int], pool: list[Parcel]
    ) -> tuple[list[Parcel], list[str]]:
        chain = [start]
        warnings: list[str] = []
        visited.add(id(start))
        current = start

        while True:
            border_text = (
                current.borders.west
                if direction is _RowDirection.EAST_TO_WEST
                else current.borders.east
            )
            if self._is_landmark(border_text):
                break
            if border_text is None or not border_text.strip():
                break

            candidates = [p for p in pool if id(p) not in visited]
            neighbor = self._find_holder_match(border_text, candidates)
            if neighbor is None:
                side = "western" if direction is _RowDirection.EAST_TO_WEST else "eastern"
                warnings.append(
                    f"No {side} neighbor found for holding "
                    f"{current.holding_id} (border text: '{border_text}')."
                )
                break

            chain.append(neighbor)
            visited.add(id(neighbor))
            current = neighbor

        return chain, warnings

    def _find_vertical_neighbor(
        self, parcel: Parcel, pool: list[Parcel], visited: set[int]
    ) -> Parcel | None:
        # القبلي (south) is tried before البحري (north), since basins are
        # conventionally read top (north) to bottom (south).
        for border_text in (parcel.borders.south, parcel.borders.north):
            if border_text is None or not border_text.strip():
                continue
            if self._is_landmark(border_text):
                continue
            candidates = [p for p in pool if id(p) not in visited]
            neighbor = self._find_holder_match(border_text, candidates)
            if neighbor is not None:
                return neighbor
        return None

    def _first_unvisited(self, pool: list[Parcel], visited: set[int]) -> Parcel | None:
        for parcel in pool:
            if id(parcel) not in visited:
                return parcel
        return None

    def _find_starting_parcel(self, parcels: list[Parcel]) -> Parcel | None:
        for parcel in parcels:
            if self._is_landmark(parcel.borders.east):
                return parcel
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
