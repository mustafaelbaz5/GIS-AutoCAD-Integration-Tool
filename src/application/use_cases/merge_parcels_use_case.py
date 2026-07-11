"""Use case: merge base and secondary sources into final parcels."""

import time
from collections.abc import Sequence

from src.application.dto.merge_result import MergeResult
from src.application.dto.parcel_record import ParcelRecord
from src.application.exceptions import PipelineCancelledError
from src.application.ports.data_source_port import DataSourcePort
from src.application.progress import IsCancelledCallback, ProgressCallback
from src.application.use_cases.compute_stats_use_case import ComputeStatsUseCase
from src.domain.entities.basin import Basin
from src.domain.entities.borders import Borders
from src.domain.entities.holder import Holder
from src.domain.entities.parcel import Parcel
from src.domain.services.spatial_sorter import SpatialSorter
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import HoldingId, normalize_for_join


class MergeParcelsUseCase:
    """Merges the base (system) source with the secondary source.

    Follows the fill-priority rules of project brief §5.4: the base
    file dictates the row set (its holding IDs are authoritative), each
    field prefers the base value and falls back to the secondary value
    except national ID (secondary-only) and the four borders plus land
    number (base-only). No field is ever fabricated.
    """

    def __init__(
        self,
        base_source: DataSourcePort,
        secondary_source: DataSourcePort,
        spatial_sorter: SpatialSorter | None = None,
    ) -> None:
        self._base_source = base_source
        self._secondary_source = secondary_source
        self._spatial_sorter = spatial_sorter

    def execute(
        self,
        on_progress: ProgressCallback | None = None,
        is_cancelled: IsCancelledCallback | None = None,
    ) -> MergeResult:
        """Run the merge (and optional spatial sort) and return the result.

        Args:
            on_progress: Optional callback invoked with (percent, message)
                as the merge advances, for a UI progress bar to bind to.
            is_cancelled: Optional callback polled periodically; when it
                returns True, raises `PipelineCancelledError` so the
                caller can unwind cleanly instead of blocking a Cancel
                request until the whole merge finishes.

        Raises:
            PipelineCancelledError: If `is_cancelled` reports cancellation.
        """

        def report(percent: int, message: str) -> None:
            if on_progress is not None:
                on_progress(percent, message)

        def check_cancelled() -> None:
            if is_cancelled is not None and is_cancelled():
                raise PipelineCancelledError

        start_time = time.time()
        report(0, "Reading base file...")
        base_records = self._base_source.read()
        report(20, f"Read {len(base_records)} base records")
        check_cancelled()

        report(25, "Reading secondary file...")
        secondary_by_key = self._index_by_join_key(self._secondary_source.read())
        report(45, "Merging records...")
        check_cancelled()

        parcels: list[Parcel] = []
        warnings: list[str] = []
        base_only_count = 0
        total = len(base_records)
        progress_step = max(1, total // 20)

        for index, base_record in enumerate(base_records, start=1):
            secondary_record = self._find_match(base_record, secondary_by_key)
            if secondary_record is None:
                base_only_count += 1
            parcel = self._build_parcel(base_record, secondary_record)
            if parcel is None:
                warnings.append("Skipped a base row with no holding ID (رقم الحيازة).")
                continue
            parcels.append(parcel)
            if index % progress_step == 0:
                report(45 + int(40 * index / total), f"Merging record {index}/{total}")
                check_cancelled()

        unplaced_count = 0
        if self._spatial_sorter is not None:
            check_cancelled()
            report(90, "Sorting parcels spatially...")
            sort_result = self._spatial_sorter.sort(parcels)
            parcels = sort_result.parcels
            warnings.extend(sort_result.warnings)
            unplaced_count = sort_result.unplaced_count

        stats = ComputeStatsUseCase().execute(
            parcels=parcels,
            base_only_count=base_only_count,
            excluded_laghi_count=self._secondary_source.excluded_count,
            unplaced_count=unplaced_count,
            elapsed_seconds=time.time() - start_time,
        )

        report(100, "Merge complete")
        return MergeResult(parcels=parcels, warnings=warnings, stats=stats)

    def _index_by_join_key(self, records: Sequence[ParcelRecord]) -> dict[str, ParcelRecord]:
        index: dict[str, ParcelRecord] = {}
        for record in records:
            if record.holding_id_raw:
                index[normalize_for_join(record.holding_id_raw)] = record
        return index

    def _find_match(
        self, base_record: ParcelRecord, secondary_by_key: dict[str, ParcelRecord]
    ) -> ParcelRecord | None:
        if not base_record.holding_id_raw:
            return None
        key = normalize_for_join(base_record.holding_id_raw)
        return secondary_by_key.get(key)

    def _build_parcel(self, base: ParcelRecord, secondary: ParcelRecord | None) -> Parcel | None:
        if not base.holding_id_raw:
            return None

        secondary_national_id = secondary.national_id if secondary else None
        secondary_holder_name = secondary.holder_name if secondary else None
        secondary_page_number = secondary.page_number if secondary else None
        secondary_directorate = secondary.directorate if secondary else None
        secondary_administration = secondary.administration if secondary else None
        secondary_basin_name = secondary.basin_name if secondary else None
        secondary_basin_code = secondary.basin_code if secondary else None
        secondary_feddan = secondary.feddan if secondary else None
        secondary_qirat = secondary.qirat if secondary else None
        secondary_sahm = secondary.sahm if secondary else None

        return Parcel(
            holding_id=HoldingId(base.holding_id_raw),
            page_number=_first_text(base.page_number, secondary_page_number),
            directorate=_first_text(base.directorate, secondary_directorate),
            administration=_first_text(base.administration, secondary_administration),
            basin=Basin(
                name=_first_text(base.basin_name, secondary_basin_name),
                code=_first_text(base.basin_code, secondary_basin_code),
            ),
            holder=Holder(
                name=_first_text(base.holder_name, secondary_holder_name),
                national_id=secondary_national_id,
            ),
            borders=Borders(
                east=base.east,
                south=base.south,
                west=base.west,
                north=base.north,
            ),
            land_number=base.land_number,
            area=Area(
                feddan=_first_number(base.feddan, secondary_feddan),
                qirat=_first_number(base.qirat, secondary_qirat),
                sahm=_first_number(base.sahm, secondary_sahm),
            ),
        )


def _first_text(*values: str | None) -> str | None:
    for value in values:
        if value is not None and value.strip() != "":
            return value
    return None


def _first_number(*values: float | None) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None
