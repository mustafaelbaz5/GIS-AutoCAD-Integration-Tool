"""Tests for infrastructure/excel/cell_parsing.py's cell-value helpers."""

from src.infrastructure.excel.cell_parsing import (
    clean_border,
    clean_text,
    normalize_national_id,
    parse_number,
)


def test_parse_number_clamps_negative_float_to_zero() -> None:
    assert parse_number(-1.0) == 0.0


def test_parse_number_clamps_negative_int_to_zero() -> None:
    assert parse_number(-19) == 0.0


def test_parse_number_clamps_negative_string_to_zero() -> None:
    assert parse_number("-4.5") == 0.0


def test_parse_number_preserves_positive_values() -> None:
    assert parse_number(13.0) == 13.0


def test_parse_number_none_stays_none() -> None:
    assert parse_number(None) is None


def test_parse_number_blank_string_stays_none() -> None:
    assert parse_number("  ") is None


def test_clean_text_strips_and_returns_none_for_blank() -> None:
    assert clean_text("  hello  ") == "hello"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_clean_border_treats_placeholders_as_none() -> None:
    assert clean_border("-") is None
    assert clean_border("،،") is None
    assert clean_border("_") is None
    assert clean_border("مصرف") == "مصرف"


def test_normalize_national_id_pads_digits_to_fourteen() -> None:
    assert normalize_national_id(26711121202206) == "26711121202206"
    assert normalize_national_id("123") == "00000000000123"
    assert normalize_national_id(None) is None
