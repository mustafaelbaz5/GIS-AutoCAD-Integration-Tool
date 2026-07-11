"""Use case: merge a primary source with a supplementary source into final parcels."""

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
    """Merges a primary source with a supplementary source.

    Follows the fill-priority rules of project brief §5.4, generalized
    per Iteration 3 §3: the primary source dictates the row set (its
    holding IDs are authoritative), each field prefers the primary
    value and falls back to the supplementary value, except national ID
    (supplementary-only) and the four borders plus land number
    (primary-only). No field is ever fabricated. Which source is
    primary vs. supplementary is decided entirely by the caller — this
    use case has no notion of "the system file" or any other special
    source.
    """

    def __init__(
        self,
        primary_source: DataSourcePort,
        supplementary_source: DataSourcePort,
        spatial_sorter: SpatialSorter | None = None,
    ) -> None:
        self._primary_source = primary_source
        self._supplementary_source = supplementary_source
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
        report(0, "Reading primary source...")
        primary_records = self._primary_source.read()
        report(20, f"Read {len(primary_records)} primary records")
        check_cancelled()

        report(25, "Reading supplementary source...")
        supplementary_by_key = self._index_by_join_key(self._supplementary_source.read())
        report(45, "Merging records...")
        check_cancelled()

        parcels: list[Parcel] = []
        warnings: list[str] = []
        primary_only_count = 0
        total = len(primary_records)
        progress_step = max(1, total // 20)

        for index, primary_record in enumerate(primary_records, start=1):
            supplementary_record = self._find_match(primary_record, supplementary_by_key)
            if supplementary_record is None:
                primary_only_count += 1
            parcel = self._build_parcel(primary_record, supplementary_record)
            if parcel is None:
                warnings.append("Skipped a primary row with no holding ID (رقم الحيازة).")
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
            primary_only_count=primary_only_count,
            excluded_laghi_count=self._supplementary_source.excluded_count,
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
        self, primary_record: ParcelRecord, supplementary_by_key: dict[str, ParcelRecord]
    ) -> ParcelRecord | None:
        if not primary_record.holding_id_raw:
            return None
        key = normalize_for_join(primary_record.holding_id_raw)
        return supplementary_by_key.get(key)

    def _build_parcel(
        self, primary: ParcelRecord, supplementary: ParcelRecord | None
    ) -> Parcel | None:
        if not primary.holding_id_raw:
            return None

        supplementary_national_id = supplementary.national_id if supplementary else None
        supplementary_holder_name = supplementary.holder_name if supplementary else None
        supplementary_page_number = supplementary.page_number if supplementary else None
        supplementary_directorate = supplementary.directorate if supplementary else None
        supplementary_administration = supplementary.administration if supplementary else None
        supplementary_basin_name = supplementary.basin_name if supplementary else None
        supplementary_basin_code = supplementary.basin_code if supplementary else None
        supplementary_feddan = supplementary.feddan if supplementary else None
        supplementary_qirat = supplementary.qirat if supplementary else None
        supplementary_sahm = supplementary.sahm if supplementary else None

        return Parcel(
            holding_id=HoldingId(primary.holding_id_raw),
            page_number=_first_text(primary.page_number, supplementary_page_number),
            directorate=_first_text(primary.directorate, supplementary_directorate),
            administration=_first_text(primary.administration, supplementary_administration),
            basin=Basin(
                name=_first_text(primary.basin_name, supplementary_basin_name),
                code=_first_text(primary.basin_code, supplementary_basin_code),
            ),
            holder=Holder(
                name=_first_text(primary.holder_name, supplementary_holder_name),
                national_id=supplementary_national_id,
            ),
            borders=Borders(
                east=primary.east,
                south=primary.south,
                west=primary.west,
                north=primary.north,
            ),
            land_number=primary.land_number,
            area=Area(
                feddan=_first_number(primary.feddan, supplementary_feddan),
                qirat=_first_number(primary.qirat, supplementary_qirat),
                sahm=_first_number(primary.sahm, supplementary_sahm),
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
