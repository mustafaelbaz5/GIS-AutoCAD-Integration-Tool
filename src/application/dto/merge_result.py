"""Result DTO for MergeParcelsUseCase."""

from dataclasses import dataclass

from src.application.dto.processing_stats import ProcessingStats
from src.domain.entities.parcel import Parcel


@dataclass(frozen=True)
class MergeResult:
    """The outcome of merging base and secondary sources.

    Args:
        parcels: The merged (and optionally spatially sorted) parcels.
        warnings: Human-readable warnings accumulated during merge and
            sorting (e.g. unmatched neighbors, rows skipped for lacking
            a holding ID). Never used to drop data silently.
        stats: Aggregate statistics for a UI statistics panel.
    """

    parcels: list[Parcel]
    warnings: list[str]
    stats: ProcessingStats
