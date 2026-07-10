"""Tests for the HoldingId value object and join-key normalization."""

import pytest
from src.domain.exceptions import InvalidHoldingIdError
from src.domain.value_objects.holding_id import HoldingId, normalize_for_join


def test_preserves_leading_zeros_for_display() -> None:
    assert str(HoldingId("010")) == "010"


def test_rejects_empty_value() -> None:
    with pytest.raises(InvalidHoldingIdError):
        HoldingId("")


def test_rejects_whitespace_only_value() -> None:
    with pytest.raises(InvalidHoldingIdError):
        HoldingId("   ")


def test_normalize_for_join_strips_leading_zeros() -> None:
    assert normalize_for_join("010") == "10"


def test_normalize_for_join_strips_whitespace() -> None:
    assert normalize_for_join("  10  ") == "10"


def test_normalize_for_join_all_zeros_collapses_to_single_zero() -> None:
    assert normalize_for_join("000") == "0"


def test_normalize_for_join_matches_across_representations() -> None:
    assert normalize_for_join("010") == normalize_for_join("10")
