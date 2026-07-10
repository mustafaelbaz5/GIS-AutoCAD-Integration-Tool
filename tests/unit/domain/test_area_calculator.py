"""Tests for AreaCalculator, per project brief §5.1."""

from src.domain.services.area_calculator import AreaCalculator
from src.domain.value_objects.area import Area


def test_feddan_only() -> None:
    assert AreaCalculator.calculate_total_sqm(Area(1, 0, 0)) == 4200.83


def test_qirat_only() -> None:
    assert AreaCalculator.calculate_total_sqm(Area(0, 1, 0)) == 175.03


def test_sahm_only() -> None:
    assert AreaCalculator.calculate_total_sqm(Area(0, 0, 1)) == 7.29


def test_all_components_combined() -> None:
    result = AreaCalculator.calculate_total_sqm(Area(2, 3, 4))
    assert result == 8955.92


def test_all_none_yields_none_not_zero() -> None:
    assert AreaCalculator.calculate_total_sqm(Area(None, None, None)) is None


def test_explicit_zeros_yield_zero_not_none() -> None:
    assert AreaCalculator.calculate_total_sqm(Area(0, 0, 0)) == 0.0


def test_partial_none_components_treated_as_zero() -> None:
    result = AreaCalculator.calculate_total_sqm(Area(1, None, None))
    assert result == 4200.83
