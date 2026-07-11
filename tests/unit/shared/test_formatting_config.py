"""Tests for FormattingConfig.column_width, per Iteration 2 Task B §5.2.A."""

from src.infrastructure.excel.formatting_config import FormattingConfig


def test_normal_column_uses_content_length_plus_two() -> None:
    config = FormattingConfig()

    assert config.column_width("اسم الحائز", max_content_length=10) == 12


def test_normal_column_caps_at_max_width() -> None:
    config = FormattingConfig()

    assert config.column_width("اسم الحائز", max_content_length=100) == 35


def test_normal_column_floors_at_min_width() -> None:
    config = FormattingConfig()

    assert config.column_width("اسم الحائز", max_content_length=1) == 8


def test_narrow_column_caps_at_twelve_even_if_content_is_longer() -> None:
    config = FormattingConfig()

    assert config.column_width("فدان", max_content_length=100) == 12


def test_narrow_column_still_uses_content_length_when_shorter_than_cap() -> None:
    config = FormattingConfig()

    assert config.column_width("رقم الحيازة", max_content_length=3) == 8


def test_national_id_column_uses_fixed_override_width() -> None:
    config = FormattingConfig()

    assert config.column_width("الرقم القومي", max_content_length=2) == 20
    assert config.column_width("الرقم القومي", max_content_length=100) == 20


def test_land_number_column_uses_fixed_override_width() -> None:
    config = FormattingConfig()

    assert config.column_width("رقم الأرض", max_content_length=2) == 16
    assert config.column_width("رقم الأرض", max_content_length=100) == 16


def test_changing_max_column_width_changes_the_result() -> None:
    default_config = FormattingConfig()
    custom_config = FormattingConfig(max_column_width=20)

    default_width = default_config.column_width("اسم الحائز", max_content_length=100)
    custom_width = custom_config.column_width("اسم الحائز", max_content_length=100)

    assert default_width == 35
    assert custom_width == 20
    assert default_width != custom_width
