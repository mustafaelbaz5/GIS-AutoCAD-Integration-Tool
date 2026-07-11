"""Main window view-model: binds the GUI to the application use cases.

Runs the pipeline synchronously for now — Phase 8 wraps `run_pipeline`
in a background QThread so the UI stays responsive during a full run.
"""

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.application.use_cases.export_final_file_use_case import ExportFinalFileUseCase
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.domain.services.spatial_sorter import SpatialSorter
from src.infrastructure.config.default_landmarks import DEFAULT_LANDMARK_KEYWORDS
from src.infrastructure.config.yaml_mapping_loader import load_mapping
from src.infrastructure.excel.base_file_reader import BaseFileReader
from src.infrastructure.excel.professional_excel_writer import (
    ProfessionalExcelWriter,
    default_output_filename,
)
from src.infrastructure.excel.secondary_file_reader import SecondaryFileReader
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper
from src.presentation.widgets.path_selector import DEFAULT_OUTPUT_DIR

_DEFAULT_MAPPINGS_DIR = (
    Path(__file__).resolve().parents[2] / "infrastructure" / "config" / "default_mappings"
)
_DEFAULT_BASE_MAPPING = _DEFAULT_MAPPINGS_DIR / "system_file_default.yaml"
_DEFAULT_SECONDARY_MAPPING = _DEFAULT_MAPPINGS_DIR / "seasonal_survey_default.yaml"


class MainViewModel(QObject):
    """Holds selection state and drives the merge/export pipeline."""

    progress_changed = Signal(int, str)
    log_emitted = Signal(str, str)  # message, level: "success" | "warning" | "error"
    finished = Signal(bool, str)  # success, output path (or empty on failure)

    def __init__(self) -> None:
        super().__init__()
        self.base_file_path: Path | None = None
        self.secondary_file_path: Path | None = None
        self.output_dir: Path = DEFAULT_OUTPUT_DIR
        self.enable_spatial_sort: bool = True

    def set_base_file(self, path: str) -> None:
        self.base_file_path = Path(path)

    def set_secondary_file(self, path: str) -> None:
        self.secondary_file_path = Path(path)

    def set_output_dir(self, path: str) -> None:
        self.output_dir = Path(path)

    @property
    def can_start(self) -> bool:
        """True once both input files have been selected."""
        return self.base_file_path is not None and self.secondary_file_path is not None

    def run_pipeline(self) -> None:
        """Run read -> merge -> sort -> write, emitting progress/log signals."""
        if not self.can_start or self.base_file_path is None or self.secondary_file_path is None:
            self.log_emitted.emit("لم يتم اختيار الملفين المطلوبين", "error")
            self.finished.emit(False, "")
            return

        try:
            output_path = self._run(self.base_file_path, self.secondary_file_path)
        except Exception as exc:  # presentation boundary: never let a raw exception escape
            self.log_emitted.emit(str(exc), "error")
            self.finished.emit(False, "")
            return

        self.finished.emit(True, str(output_path))

    def _run(self, base_file_path: Path, secondary_file_path: Path) -> Path:
        base_config = load_mapping(_DEFAULT_BASE_MAPPING)
        secondary_config = load_mapping(_DEFAULT_SECONDARY_MAPPING)

        base_reader = BaseFileReader(base_file_path, base_config)
        secondary_mapper = YamlColumnMapper(secondary_config["fields"])
        secondary_reader = SecondaryFileReader(
            secondary_file_path, secondary_mapper, secondary_config
        )
        sorter = SpatialSorter(DEFAULT_LANDMARK_KEYWORDS) if self.enable_spatial_sort else None

        result = MergeParcelsUseCase(base_reader, secondary_reader, sorter).execute(
            on_progress=self._emit_progress
        )
        self.log_emitted.emit(f"تم دمج {len(result.parcels)} حيازة", "success")
        for warning in result.warnings:
            self.log_emitted.emit(warning, "warning")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / default_output_filename()
        ExportFinalFileUseCase(ProfessionalExcelWriter()).execute(
            result.parcels, output_path, on_progress=self._emit_progress
        )
        self.log_emitted.emit(f"تم حفظ الملف: {output_path}", "success")
        return output_path

    def _emit_progress(self, percent: int, message: str) -> None:
        self.progress_changed.emit(percent, message)
