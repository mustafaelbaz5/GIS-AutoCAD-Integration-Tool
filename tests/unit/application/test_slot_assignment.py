"""Tests for the SlotAssignment DTO."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from src.application.dto.slot_assignment import SlotAssignment
from src.domain.value_objects.slot_role import SlotRole


def test_holds_role_file_path_and_mapping_path() -> None:
    assignment = SlotAssignment(
        role=SlotRole.PRIMARY,
        file_path=Path("base.xlsx"),
        mapping_path=Path("system_file_default.yaml"),
    )

    assert assignment.role == SlotRole.PRIMARY
    assert assignment.file_path == Path("base.xlsx")
    assert assignment.mapping_path == Path("system_file_default.yaml")


def test_is_frozen() -> None:
    assignment = SlotAssignment(
        role=SlotRole.SUPPLEMENTARY,
        file_path=Path("external.xlsx"),
        mapping_path=Path("external_file_default.yaml"),
    )

    with pytest.raises(FrozenInstanceError):
        assignment.role = SlotRole.PRIMARY  # type: ignore[misc]
