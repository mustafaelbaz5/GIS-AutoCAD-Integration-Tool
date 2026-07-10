"""Tests for the fuzzy_matcher wrapper around rapidfuzz."""

from src.shared.fuzzy_matcher import best_match, similarity


def test_best_match_returns_exact_match() -> None:
    assert best_match("احمد محمد", ["احمد محمد", "سالم على"]) == "احمد محمد"


def test_best_match_tolerates_minor_typos() -> None:
    result = best_match("احمد محمد", ["احمد محمود", "سالم على"], threshold=70)
    assert result == "احمد محمود"


def test_best_match_returns_none_below_threshold() -> None:
    result = best_match("احمد محمد", ["سالم على تماما مختلف"], threshold=90)
    assert result is None


def test_best_match_returns_none_for_empty_candidates() -> None:
    assert best_match("احمد", []) is None


def test_best_match_returns_none_for_empty_query() -> None:
    assert best_match("", ["احمد"]) is None


def test_similarity_identical_strings_is_100() -> None:
    assert similarity("احمد", "احمد") == 100.0
