"""Tests for the MergeOptions DTO."""

from src.application.dto.merge_options import MergeOptions


def test_defaults_match_the_established_iteration_2_behavior() -> None:
    options = MergeOptions()

    assert options.include_laghi_rows is False
    assert options.enable_spatial_sort is True


def test_can_override_both_fields() -> None:
    options = MergeOptions(include_laghi_rows=True, enable_spatial_sort=False)

    assert options.include_laghi_rows is True
    assert options.enable_spatial_sort is False
