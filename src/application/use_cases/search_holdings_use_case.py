"""Use case: search holdings by holder name or holding ID.

Pure computation, no I/O — operates on an in-memory `list[Parcel]`
already loaded via `OutputFileSourcePort`. Per Iteration 2 Task C §6.4:
numeric queries match the holding ID (exact prefix first, then
contains); text queries fuzzy-match the holder name after Arabic
normalization.
"""

from collections.abc import Sequence

from src.application.dto.search_result import SearchMatch
from src.domain.entities.parcel import Parcel
from src.shared.arabic_normalizer import normalize_arabic
from src.shared.fuzzy_matcher import weighted_similarity

DEFAULT_MAX_RESULTS = 10
DEFAULT_NAME_MATCH_THRESHOLD = 70.0
_HOLDING_ID_PREFIX_SCORE = 100.0
_HOLDING_ID_CONTAINS_SCORE = 50.0


class SearchHoldingsUseCase:
    """Filters and ranks a parcel list by holder name or holding ID."""

    def execute(
        self,
        parcels: Sequence[Parcel],
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        name_match_threshold: float = DEFAULT_NAME_MATCH_THRESHOLD,
    ) -> list[SearchMatch]:
        """Return up to `max_results` matches, ranked by relevance.

        Args:
            parcels: The full in-memory dataset to search.
            query: The user's search text.
            max_results: Maximum number of grouped suggestions to return.
            name_match_threshold: Minimum WRatio score (0-100) for a
                holder-name match to be included.
        """
        query = query.strip()
        if not query:
            return []

        if query.isdigit():
            scores = self._score_by_holding_id(parcels, query)
        else:
            scores = self._score_by_holder_name(parcels, query, name_match_threshold)

        return self._group_and_rank(parcels, scores, max_results)

    def find_best_name_match(
        self,
        parcels: Sequence[Parcel],
        name: str,
        threshold: float = DEFAULT_NAME_MATCH_THRESHOLD,
    ) -> Parcel | None:
        """Return the single best holder-name match, if above `threshold`.

        Used for "clicking a neighbor" navigation from a border's text.
        """
        scores = self._score_by_holder_name(parcels, name, threshold)
        if not scores:
            return None
        best_index = max(scores, key=lambda index: scores[index])
        return parcels[best_index]

    def _score_by_holding_id(self, parcels: Sequence[Parcel], query: str) -> dict[int, float]:
        scores: dict[int, float] = {}
        for index, parcel in enumerate(parcels):
            holding_id_text = str(parcel.holding_id)
            if holding_id_text.startswith(query):
                scores[index] = _HOLDING_ID_PREFIX_SCORE
            elif query in holding_id_text:
                scores[index] = _HOLDING_ID_CONTAINS_SCORE
        return scores

    def _score_by_holder_name(
        self, parcels: Sequence[Parcel], query: str, threshold: float
    ) -> dict[int, float]:
        normalized_query = normalize_arabic(query)
        scores: dict[int, float] = {}
        for index, parcel in enumerate(parcels):
            name = parcel.holder.name
            if not name:
                continue
            score = weighted_similarity(normalized_query, normalize_arabic(name))
            if score >= threshold:
                scores[index] = score
        return scores

    def _group_and_rank(
        self,
        parcels: Sequence[Parcel],
        scores: dict[int, float],
        max_results: int,
    ) -> list[SearchMatch]:
        best_score_by_holding_id: dict[str, float] = {}
        for index, score in scores.items():
            key = str(parcels[index].holding_id)
            if score > best_score_by_holding_id.get(key, -1.0):
                best_score_by_holding_id[key] = score

        grouped_parcels: dict[str, list[Parcel]] = {key: [] for key in best_score_by_holding_id}
        for parcel in parcels:
            key = str(parcel.holding_id)
            if key in grouped_parcels:
                grouped_parcels[key].append(parcel)

        matches = [
            SearchMatch(
                holding_id=key,
                holder_name=group[0].holder.name if group else None,
                parcels=group,
                score=best_score_by_holding_id[key],
            )
            for key, group in grouped_parcels.items()
        ]
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:max_results]
