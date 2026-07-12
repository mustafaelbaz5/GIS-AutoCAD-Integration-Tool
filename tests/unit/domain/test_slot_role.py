"""Tests for the SlotRole value object."""

from src.domain.value_objects.slot_role import SlotRole


def test_has_exactly_two_roles() -> None:
    assert {role.value for role in SlotRole} == {"primary", "supplementary"}


def test_roles_are_distinct() -> None:
    assert SlotRole.PRIMARY != SlotRole.SUPPLEMENTARY
