"""Tests for the Area value object."""

import pytest
from src.domain.exceptions import InvalidAreaError
from src.domain.value_objects.area import Area


def test_is_empty_true_when_all_none() -> None:
    assert Area(None, None, None).is_empty


def test_is_empty_false_when_any_component_present() -> None:
    assert not Area(0, None, None).is_empty


def test_rejects_negative_feddan() -> None:
    with pytest.raises(InvalidAreaError):
        Area(-1, 0, 0)


def test_rejects_negative_qirat() -> None:
    with pytest.raises(InvalidAreaError):
        Area(0, -1, 0)


def test_rejects_negative_sahm() -> None:
    with pytest.raises(InvalidAreaError):
        Area(0, 0, -1)


def test_accepts_zero_components() -> None:
    area = Area(0, 0, 0)
    assert not area.is_empty
