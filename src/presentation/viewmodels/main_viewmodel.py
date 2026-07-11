"""Main window view-model: binds the GUI to the application use cases."""

from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, Signal

from src.application.exceptions import PipelineCancelledError
from src.application.use_cases.export_final_file_use_case import ExportFinalFileUseCase
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.domain.services.spatial_sorter import SpatialSorter
from src.infrastructure.config.default_landmarks import DEFAULT_LANDMARK_KEYWORDS
from src.infrastructure.config.yaml_mapping_loader import load_mapping
from src.infrastructure.excel.base_file_reader import BaseFileReader
from src.infrastructure.excel.professional_excel_writer import (
    ProfessionalExcelWriter,
    default_output_filename,
    resolve_unique_path,
)
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper
from src.presentation.i18n.ar import (
    CANCELLED_MESSAGE,
    FILE_SAVED_MESSAGE,
    GENERIC_PROCESSING_ERROR,
    MERGE_SUCCESS_MESSAGE,
    NO_FILES_SELECTED_ERROR,
)
from src.presentation.widgets.path_selector import DEFAULT_OUTPUT_DIR
from src.shared.paths import get_app_root

_DEFAULT_MAPPINGS_DIR = get_app_root() / "src" / "infrastructure" / "config" / "default_mappings"
_DEFAULT_BASE_MAPPING = _DEFAULT_MAPPINGS_DIR / "system_file_default.yaml"
_DEFAULT_SECONDARY_MAPPING = _DEFAULT_MAPPINGS_DIR / "seasonal_survey_default.yaml"


class MainViewModel(QObject):
    """Holds selection state and drives the merge/export pipeline.

    Designed to run on a background `QThread` (see
    `presentation/workers/pipeline_worker.py`) so the GUI thread stays
    responsive; `request_cancel()` is safe to call from the GUI thread
    while `run_pipeline()` executes on the worker thread, since it only
    flips a plain bool flag the use cases poll cooperatively.
    """

    progress_changed = Signal(int, str)
    log_emitted = Signal(str, str)  # message, level: "success" | "warning" | "error"
    finished = Signal(bool, str)  # success, output path (or empty on failure/cancel)
    stats_ready = Signal(object)  # ProcessingStats, emitted just before `finished(True, ...)`

    def __init__(self) -> None:
        super().__init__()
        self.base_file_path: Path | None = None
        self.secondary_file_path: Path | None = None
        self.output_dir: Path = DEFAULT_OUTPUT_DIR
        self.enable_spatial_sort: bool = True
        self.include_laghi_rows: bool = False
        self.secondary_mapping_path: Path | None = None
        self._cancel_requested = False

    def set_base_file(self, path: str) -> None:
        self.base_file_path = Path(path)

    def set_secondary_file(self, path: str) -> None:
        self.secondary_file_path = Path(path)

    def set_output_dir(self, path: str) -> None:
        self.output_dir = Path(path)

    def request_cancel(self) -> None:
        """Request cancellation of an in-progress `run_pipeline()` call."""
        self._cancel_requested = True

    def reset_cancel_flag(self) -> None:
        """Clear any pending cancellation before starting a new run.

        Must be called from the GUI thread before the worker thread is
        started (not from inside `run_pipeline()` itself) — otherwise a
        Cancel click issued right after Start can race with the worker
        thread's startup and have its flag-set silently clobbered by a
        reset that runs after it.
        """
        self._cancel_requested = False

    @property
    def can_start(self) -> bool:
        """True once both input files have been selected."""
        return self.base_file_path is not None and self.secondary_file_path is not None

    def run_pipeline(self) -> None:
        """Run read -> merge -> sort -> write, emitting progress/log signals.

        Every failure is caught here and surfaced as a friendly Arabic
        message via `log_emitted` — no raw exception text ever reaches
        the user. Technical details go to the (English) developer log.
        """
        if not self.can_start or self.base_file_path is None or self.secondary_file_path is None:
            self.log_emitted.emit(NO_FILES_SELECTED_ERROR, "error")
            self.finished.emit(False, "")
            return

        try:
            output_path = self._run(self.base_file_path, self.secondary_file_path)
        except PipelineCancelledError:
            logger.info("Pipeline cancelled by user.")
            self.log_emitted.emit(CANCELLED_MESSAGE, "warning")
            self.finished.emit(False, "")
            return
        except Exception as exc:  # presentation boundary: never let a raw exception escape
            logger.error(f"Pipeline failed: {exc}")
            self.log_emitted.emit(GENERIC_PROCESSING_ERROR, "error")
            self.finished.emit(False, "")
            return

        self.finished.emit(True, str(output_path))

    def _run(self, base_file_path: Path, secondary_file_path: Path) -> Path:
        base_config = load_mapping(_DEFAULT_BASE_MAPPING)
        secondary_mapping_path = self.secondary_mapping_path or _DEFAULT_SECONDARY_MAPPING
        secondary_config = load_mapping(secondary_mapping_path)

        base_reader = BaseFileReader(base_file_path, base_config)
        secondary_mapper = YamlColumnMapper(secondary_config["fields"])
        secondary_reader = SecondaryFileReader(
            secondary_file_path,
            secondary_mapper,
            secondary_config,
            apply_exclusion=not self.include_laghi_rows,
        )
        sorter = SpatialSorter(DEFAULT_LANDMARK_KEYWORDS) if self.enable_spatial_sort else None

        result = MergeParcelsUseCase(base_reader, secondary_reader, sorter).execute(
            on_progress=self._emit_progress, is_cancelled=self._is_cancelled
        )
        self.log_emitted.emit(MERGE_SUCCESS_MESSAGE.format(count=len(result.parcels)), "success")
        for warning in result.warnings:
            self.log_emitted.emit(warning, "warning")
        self.stats_ready.emit(result.stats)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = resolve_unique_path(self.output_dir / default_output_filename())
        ExportFinalFileUseCase(ProfessionalExcelWriter()).execute(
            result.parcels,
            output_path,
            on_progress=self._emit_progress,
            is_cancelled=self._is_cancelled,
        )
        self.log_emitted.emit(FILE_SAVED_MESSAGE.format(path=output_path), "success")
        return output_path

    def _emit_progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)

    def _is_cancelled(self) -> bool:
        return self._cancel_requested
