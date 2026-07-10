"""Tests for arabic_normalizer, per project brief §5.6."""

from src.shared.arabic_normalizer import normalize_arabic


def test_normalizes_alef_maksura_to_ya() -> None:
    assert normalize_arabic("مصطفى") == normalize_arabic("مصطفي")


def test_normalizes_hamza_variants_to_bare_alef() -> None:
    assert normalize_arabic("أحمد") == normalize_arabic("احمد")
    assert normalize_arabic("إحمد") == normalize_arabic("احمد")
    assert normalize_arabic("آحمد") == normalize_arabic("احمد")


def test_removes_diacritics() -> None:
    assert normalize_arabic("مُحَمَّد") == normalize_arabic("محمد")


def test_collapses_repeated_whitespace() -> None:
    assert normalize_arabic("احمد   محمد") == "احمد محمد"


def test_strips_leading_and_trailing_whitespace() -> None:
    assert normalize_arabic("  احمد  ") == "احمد"


def test_taa_marbuta_untouched_by_default() -> None:
    assert normalize_arabic("مدرسة") == "مدرسة"


def test_taa_marbuta_normalized_when_toggled() -> None:
    assert normalize_arabic("مدرسة", normalize_taa_marbuta=True) == "مدرسه"


def test_exclusion_value_variants_match_after_normalization() -> None:
    assert normalize_arabic("لاغى") == normalize_arabic("لاغي")
