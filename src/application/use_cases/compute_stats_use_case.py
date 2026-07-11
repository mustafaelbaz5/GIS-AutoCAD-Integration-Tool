"""Use case: compute processing statistics from a merged parcel list.

Pure computation, no I/O — reads only the `Parcel` entities already in
memory. Intentionally does not import `output_schema.py` (the Excel
writer's column definitions) to avoid an application -> infrastructure
dependency; field labels are declared locally instead.
"""

from collections import Counter
from collections.abc import Sequence

from src.application.dto.processing_stats import ProcessingStats
from src.domain.entities.parcel import Parcel
from src.domain.services.area_calculator import AreaCalculator

_FIELD_LABELS: dict[str, str] = {
    "page_number": "رقم الصفحة بالسجل",
    "directorate": "المديريه",
    "administration": "الأداره",
    "basin_name": "اسم الحوض",
    "basin_code": "كود الحوض",
    "holder_name": "اسم الحائز",
    "national_id": "الرقم القومي",
    "east": "الحد الشرقى",
    "south": "الحد القبلى",
    "west": "الحد الغربى",
    "north": "الحد البحرى",
    "land_number": "رقم الأرض",
    "feddan": "فدان",
    "qirat": "قيراط",
    "sahm": "سهم",
}


class ComputeStatsUseCase:
    """Computes `ProcessingStats` from a merged parcel list."""

    def execute(
        self,
        parcels: Sequence[Parcel],
        primary_only_count: int,
        excluded_laghi_count: int,
        unplaced_count: int,
        elapsed_seconds: float,
    ) -> ProcessingStats:
        """Compute aggregate statistics for a completed merge run."""
        empty_field_counts: Counter[str] = Counter()
        complete_rows = 0
        incomplete_holding_ids: list[str] = []
        with_national_id = 0
        total_feddan = 0.0
        total_sqm = 0.0
        basin_counts: Counter[str] = Counter()

        for parcel in parcels:
            empty_fields = [
                name for name, value in self._field_values(parcel).items() if _is_empty(value)
            ]
            if empty_fields:
                empty_field_counts.update(empty_fields)
                incomplete_holding_ids.append(str(parcel.holding_id))
            else:
                complete_rows += 1

            if parcel.holder.national_id:
                with_national_id += 1

            total_feddan += parcel.area.feddan or 0.0
            total_sqm += AreaCalculator.calculate_total_sqm(parcel.area) or 0.0

            if parcel.basin.name:
                basin_counts[parcel.basin.name] += 1

        total = len(parcels)
        top_empty = [
            (_FIELD_LABELS[name], count) for name, count in empty_field_counts.most_common(3)
        ]

        return ProcessingStats(
            total_merged=total,
            complete_rows=complete_rows,
            incomplete_rows=total - complete_rows,
            incomplete_holding_ids=incomplete_holding_ids,
            most_often_empty_fields=top_empty,
            primary_only_count=primary_only_count,
            supplementary_only_count=0,
            with_national_id=with_national_id,
            without_national_id=total - with_national_id,
            excluded_laghi_count=excluded_laghi_count,
            total_feddan=round(total_feddan, 2),
            total_sqm=round(total_sqm, 2),
            distinct_basin_count=len(basin_counts),
            top_basins=list(basin_counts.most_common(3)),
            unplaced_count=unplaced_count,
            elapsed_seconds=round(elapsed_seconds, 2),
        )

    def _field_values(self, parcel: Parcel) -> dict[str, object]:
        return {
            "page_number": parcel.page_number,
            "directorate": parcel.directorate,
            "administration": parcel.administration,
            "basin_name": parcel.basin.name,
            "basin_code": parcel.basin.code,
            "holder_name": parcel.holder.name,
            "national_id": parcel.holder.national_id,
            "east": parcel.borders.east,
            "south": parcel.borders.south,
            "west": parcel.borders.west,
            "north": parcel.borders.north,
            "land_number": parcel.land_number,
            "feddan": parcel.area.feddan,
            "qirat": parcel.area.qirat,
            "sahm": parcel.area.sahm,
        }


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip() == ""
