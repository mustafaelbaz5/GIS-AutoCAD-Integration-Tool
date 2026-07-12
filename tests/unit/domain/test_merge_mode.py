"""Tests for the MergeMode value object."""

from src.domain.value_objects.merge_mode import MergeMode


def test_has_exactly_two_modes() -> None:
    assert {mode.value for mode in MergeMode} == {"system_plus_external", "two_external"}


def test_modes_are_distinct() -> None:
    assert MergeMode.SYSTEM_PLUS_EXTERNAL != MergeMode.TWO_EXTERNAL
