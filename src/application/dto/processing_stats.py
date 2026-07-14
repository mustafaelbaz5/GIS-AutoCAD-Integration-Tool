"""DTO summarizing a completed merge run, for a UI statistics panel."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessingStats:
    """Aggregate statistics computed from a merged parcel list.

    Args:
        total_merged: Total rows in the output.
        complete_rows: Rows where every field has a value.
        incomplete_rows: Rows with at least one empty field.
        incomplete_holding_ids: Holding IDs of the incomplete rows, for
            a UI drill-down (e.g. a "which rows?" popover).
        most_often_empty_fields: Up to 3 (Arabic field label, count)
            pairs, the fields most often left empty.
        primary_only_count: Rows with no match in the supplementary source.
        supplementary_only_count: Rows that existed only in the
            supplementary source (always 0, since the merge is
            primary-driven — kept for transparency in the UI).
        with_national_id: Rows with a national ID.
        without_national_id: Rows missing a national ID.
        excluded_laghi_count: Rows the exclusion rule filtered out.
        total_feddan: Sum of the فدان column.
        total_sqm: Sum of the computed total-area (م²) column.
        distinct_basin_count: Distinct basin names.
        top_basins: Up to 3 (basin name, parcel count) pairs, largest first.
        elapsed_seconds: Wall-clock time the merge took.
    """

    total_merged: int
    complete_rows: int
    incomplete_rows: int
    incomplete_holding_ids: list[str]
    most_often_empty_fields: list[tuple[str, int]]
    primary_only_count: int
    supplementary_only_count: int
    with_national_id: int
    without_national_id: int
    excluded_laghi_count: int
    total_feddan: float
    total_sqm: float
    distinct_basin_count: int
    top_basins: list[tuple[str, int]]
    elapsed_seconds: float
