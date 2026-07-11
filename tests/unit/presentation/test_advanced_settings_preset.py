"""Tests for AdvancedSettings preset serialization (save/load), per §9."""

from src.presentation.widgets.advanced_settings_panel import AdvancedSettings


def test_round_trips_through_json() -> None:
    original = AdvancedSettings(
        secondary_mapping_path="/some/path/mapping.yaml",
        include_laghi_rows=True,
        enable_spatial_sort=False,
    )

    restored = AdvancedSettings.from_json(original.to_json())

    assert restored == original


def test_default_settings_round_trip() -> None:
    original = AdvancedSettings()

    restored = AdvancedSettings.from_json(original.to_json())

    assert restored == original
