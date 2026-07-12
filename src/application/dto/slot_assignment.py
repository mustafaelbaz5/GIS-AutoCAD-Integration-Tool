"""Slot assignment DTO, per Iteration 3 Task B."""

from dataclasses import dataclass
from pathlib import Path

from src.domain.value_objects.slot_role import SlotRole


@dataclass(frozen=True)
class SlotAssignment:
    """A fully-resolved (file, mapping, role) triple for one input slot.

    The presentation layer builds two of these (per `MergeMode`) before
    constructing readers and invoking `MergeParcelsUseCase` — see
    `presentation/api/main_api.py`. Neither `SlotAssignment` nor
    `MergeParcelsUseCase` needs to know which `MergeMode` produced it;
    by the time a `SlotAssignment` exists, the mode's job (constraining
    which mappings were choosable) is already done.
    """

    role: SlotRole
    file_path: Path
    mapping_path: Path
