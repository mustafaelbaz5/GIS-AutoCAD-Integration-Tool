"""Slot role value object, per Iteration 3 Task B."""

from enum import Enum


class SlotRole(Enum):
    """Which merge role a file slot plays.

    Independent of *what kind* of file/mapping is assigned to a slot —
    a slot's role only says how `MergeParcelsUseCase` treats it: the
    primary slot's holding IDs are authoritative (dictate the row set)
    and its fields win conflicts; the supplementary slot fills gaps.
    See `MergeParcelsUseCase`'s docstring for the full fill-priority
    rule this drives.
    """

    PRIMARY = "primary"
    SUPPLEMENTARY = "supplementary"
