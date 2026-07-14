"""Merge options DTO, per Iteration 3 Task B.

Consolidates the cross-cutting Advanced Settings toggles (previously
two loose booleans tracked ad hoc by the PySide6 view-model) into one
value passed alongside the two `SlotAssignment`s.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MergeOptions:
    """Advanced Settings state that shapes how a merge run behaves.

    Does not include file/mapping choices — those live on the two
    `SlotAssignment`s.
    """

    include_laghi_rows: bool = False
    """When True, rows the supplementary mapping's exclusion rule would
    normally drop (e.g. القاصر == "لاغى") are kept instead."""

    enable_spatial_sort: bool = True
    """When True, `MergeParcelsUseCase` is given a `BasinSorter` so
    output rows are ordered alphabetically (A→Z) by holder name
    (اسم الحائز) within each basin, rather than source-file order."""
