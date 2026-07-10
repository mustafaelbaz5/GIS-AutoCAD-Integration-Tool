"""Thin wrapper around `rapidfuzz` for fuzzy string matching.

Isolated here so that domain services depend on this single seam rather
than importing `rapidfuzz` directly, keeping the fuzzy-matching library
swappable.
"""

from collections.abc import Iterable

from rapidfuzz import fuzz, process

DEFAULT_MATCH_THRESHOLD = 85.0


def best_match(
    query: str,
    candidates: Iterable[str],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> str | None:
    """Return the candidate most similar to `query`, if above `threshold`.

    Args:
        query: The text to match against the candidate pool.
        candidates: Candidate strings to search.
        threshold: Minimum similarity score (0-100) to accept a match.

    Returns:
        The best-matching candidate, or None if no candidate meets the
        threshold.
    """
    candidate_list = list(candidates)
    if not query or not candidate_list:
        return None
    result = process.extractOne(query, candidate_list, scorer=fuzz.ratio)
    if result is None:
        return None
    match, score, _ = result
    return match if score >= threshold else None


def similarity(a: str, b: str) -> float:
    """Return the similarity ratio (0-100) between two strings."""
    return fuzz.ratio(a, b)
