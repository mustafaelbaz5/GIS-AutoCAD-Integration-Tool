"""DTO for a single search suggestion, per Iteration 2 Task C."""

from dataclasses import dataclass

from src.domain.entities.parcel import Parcel


@dataclass(frozen=True)
class SearchMatch:
    """One autocomplete suggestion, grouped by holding ID.

    A holder can own several parcels (several رقم الأرض) under the same
    holding ID; the search UI shows one suggestion per holding ID, and
    `parcels` holds every parcel in that group so the caller can show a
    sub-picker when there's more than one.

    Args:
        holding_id: The (already-normalized-for-display) holding ID text.
        holder_name: The holder's name, for the suggestion label.
        parcels: All parcels sharing this holding ID (length >= 1).
        score: Match relevance (0-100), used for ranking.
    """

    holding_id: str
    holder_name: str | None
    parcels: list[Parcel]
    score: float
