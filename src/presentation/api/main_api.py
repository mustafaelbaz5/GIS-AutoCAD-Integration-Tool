"""Python-side bridge exposed to the main window's JavaScript.

Every public method here becomes callable from JS as
`window.pywebview.api.<method_name>(...)`, per Iteration 4. Real
processing (Task D) mirrors exactly what the old PySide6
`main_viewmodel.py` did, just pushed to JS instead of emitted as Qt
signals: build two `SlotAssignment`s + a `MergeOptions` from the
selected files/settings, construct `MappedFileReader`s, run
`MergeParcelsUseCase` then `ExportFinalFileUseCase` on a background
thread, and push progress/completion back via `evaluate_js`.
"""

import json
import os
import threading
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

import openpyxl
import webview
from loguru import logger
from src.application.dto.merge_options import MergeOptions
from src.application.dto.slot_assignment import SlotAssignment
from src.application.exceptions import PipelineCancelledError
from src.application.use_cases.export_final_file_use_case import ExportFinalFileUseCase
from src.application.use_cases.merge_parcels_use_case import MergeParcelsUseCase
from src.domain.services.spatial_sorter import SpatialSorter
from src.domain.value_objects.slot_role import SlotRole
from src.infrastructure.config.app_settings import (
    DEFAULT_OUTPUT_DIR,
    load_last_output_dir,
    save_last_output_dir,
)
from src.infrastructure.config.default_landmarks import DEFAULT_LANDMARK_KEYWORDS
from src.infrastructure.config.yaml_mapping_loader import list_available_mappings, load_mapping
from src.infrastructure.excel.mapped_file_reader import MappedFileReader, read_first_field_value
from src.infrastructure.excel.professional_excel_writer import (
    ProfessionalExcelWriter,
    build_output_filename,
    resolve_unique_path,
)
from src.infrastructure.excel.yaml_column_mapper import YamlColumnMapper
from src.shared.paths import get_app_root

_DEFAULT_MAPPINGS_DIR = get_app_root() / "src" / "infrastructure" / "config" / "default_mappings"
_DEFAULT_SYSTEM_MAPPING = _DEFAULT_MAPPINGS_DIR / "system_file_default.yaml"
_DEFAULT_EXTERNAL_MAPPING = _DEFAULT_MAPPINGS_DIR / "external_file_default.yaml"

_INVALID_EXTENSION_ERROR = "الملف يجب أن يكون بصيغة xlsx"
_FILE_NOT_FOUND_ERROR = "تعذر العثور على الملف"
_FILE_READ_ERROR = "تعذر قراءة الملف"
_NO_FILES_SELECTED_ERROR = "الرجاء اختيار الملفين المطلوبين أولاً"
_GENERIC_PROCESSING_ERROR = "حدث خطأ غير متوقع أثناء المعالجة. راجع سجل العمليات لمزيد من التفاصيل."


class MainApi:
    """JS-callable API for the main window. See module docstring."""

    def __init__(self, open_search_window: Callable[[Path | None], None]) -> None:
        """Args:
        open_search_window: Callback that creates/focuses the search
            window, given the last generated output path (or None if
            no merge has completed yet this session). Injected rather
            than imported directly, so this class doesn't need to know
            how window creation is wired.
        """
        self._window: webview.Window | None = None
        self._open_search_window = open_search_window
        self._cancel_requested = False
        self._output_dir: Path = load_last_output_dir() or DEFAULT_OUTPUT_DIR
        self._last_output_path: Path | None = None
        self._log_sink_id: int | None = None

    def bind_window(self, window: webview.Window) -> None:
        """Attach the `webview.Window` this API instance belongs to.

        Called once, immediately after `webview.create_window()`
        returns, from `app_window.py`. Also installs a loguru sink
        that streams log messages to JS, per Task D's log-panel
        requirement.
        """
        self._window = window
        self._log_sink_id = logger.add(self._log_sink, level="INFO", format="{message}")

    def _log_sink(self, message: Any) -> None:
        record = message.record
        self._push_event(
            "onLogMessage", {"level": record["level"].name, "message": record["message"]}
        )

    def select_file(self, slot: str) -> dict[str, Any]:
        """Open a native file picker for the given drop-zone slot.

        `slot` is `"base"` or `"secondary"`, matching the two drop
        zones (ملف المنظومة / الملف الخارجي).
        """
        logger.info(f"select_file called for slot={slot!r}")
        if self._window is None:
            return {"error": "Window not ready"}

        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=("Excel Files (*.xlsx)", "All files (*.*)"),
        )
        if not result:
            return {"cancelled": True}

        return self._validate_file(slot, Path(result[0]))

    def handle_dropped_file(self, slot: str, file_path: str) -> dict[str, Any]:
        """Validate a file dropped onto a drop-zone via HTML5 drag & drop."""
        logger.info(f"handle_dropped_file called for slot={slot!r}, path={file_path!r}")
        return self._validate_file(slot, Path(file_path))

    def _validate_file(self, slot: str, path: Path) -> dict[str, Any]:
        """Lightweight validation: extension + a row-count peek.

        Mirrors the old PySide6 `DropZone`'s validation exactly (not a
        full `MappedFileReader` parse, which needs a specific mapping
        chosen first — that happens at `start_processing` time). A
        workbook missing a `<dimension>` tag reports `max_row` as None
        even though it reads fine; that's not an error, just missing
        metadata.
        """
        if path.suffix.lower() != ".xlsx":
            return {"slot": slot, "valid": False, "error": _INVALID_EXTENSION_ERROR}
        if not path.exists():
            return {"slot": slot, "valid": False, "error": _FILE_NOT_FOUND_ERROR}

        try:
            workbook = openpyxl.load_workbook(path, read_only=True)
            sheet = workbook.active
            row_count = sheet.max_row if sheet is not None else None
        except Exception:
            logger.exception(f"Failed to open {path} for validation")
            return {"slot": slot, "valid": False, "error": _FILE_READ_ERROR}

        return {
            "slot": slot,
            "valid": True,
            "path": str(path),
            "name": path.name,
            "row_count": row_count,
        }

    def clear_files(self) -> None:
        """No server-side file state to reset — JS owns selection state.

        Kept as a real (non-stub) round-trip target since the Actions
        Bar's مسح button always calls it; logged for parity with the
        rest of the pipeline's log stream.
        """
        logger.info("clear_files called")

    def get_output_dir(self) -> str:
        """Return the current output directory (last-used, or the default).

        Called once at startup so JS never hardcodes a path — the
        Stitch mockups show a placeholder path
        (`C:\\Users\\Admin\\Desktop\\GIS_Output`) for illustration only.
        """
        return str(self._output_dir)

    def list_secondary_mappings(self) -> list[dict[str, Any]]:
        """List available mappings for the external/secondary slot.

        Populates the Advanced Settings mapping picker. The base/system
        slot's mapping is always `system_file_default.yaml` in
        SYSTEM_PLUS_EXTERNAL mode (the only mode with a UI so far — see
        resources/design/INVENTORY.md), so it isn't offered here.
        """
        mappings = list_available_mappings(_DEFAULT_MAPPINGS_DIR)
        return [
            {
                "path": str(m.path),
                "name": m.name,
                "description": m.description,
                "is_default": m.path == _DEFAULT_EXTERNAL_MAPPING,
            }
            for m in mappings
        ]

    def start_processing(
        self,
        base_path: str,
        secondary_path: str,
        secondary_mapping_path: str | None,
        output_dir: str,
        include_laghi_rows: bool,
        enable_spatial_sort: bool,
    ) -> None:
        """Kick off the real merge pipeline on a background thread.

        Must not block the webview UI thread — progress is pushed back
        via `evaluate_js` as the merge runs.
        """
        logger.info(f"start_processing called: base={base_path!r}, secondary={secondary_path!r}")
        if not base_path or not secondary_path:
            self._push_event("onMergeFailed", {"message": _NO_FILES_SELECTED_ERROR})
            return

        self._cancel_requested = False
        self._output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        mapping_path = (
            Path(secondary_mapping_path) if secondary_mapping_path else (_DEFAULT_EXTERNAL_MAPPING)
        )
        options = MergeOptions(
            include_laghi_rows=include_laghi_rows, enable_spatial_sort=enable_spatial_sort
        )
        primary_slot = SlotAssignment(
            role=SlotRole.PRIMARY, file_path=Path(base_path), mapping_path=_DEFAULT_SYSTEM_MAPPING
        )
        supplementary_slot = SlotAssignment(
            role=SlotRole.SUPPLEMENTARY, file_path=Path(secondary_path), mapping_path=mapping_path
        )

        thread = threading.Thread(
            target=self._run_merge,
            args=(primary_slot, supplementary_slot, options),
            daemon=True,
        )
        thread.start()

    def _run_merge(
        self,
        primary_slot: SlotAssignment,
        supplementary_slot: SlotAssignment,
        options: MergeOptions,
    ) -> None:
        try:
            primary_config = load_mapping(primary_slot.mapping_path)
            supplementary_config = load_mapping(supplementary_slot.mapping_path)

            primary_mapper = YamlColumnMapper(primary_config["fields"])
            primary_reader = MappedFileReader(
                primary_slot.file_path, primary_mapper, primary_config
            )
            supplementary_mapper = YamlColumnMapper(supplementary_config["fields"])
            supplementary_reader = MappedFileReader(
                supplementary_slot.file_path,
                supplementary_mapper,
                supplementary_config,
                apply_exclusion=not options.include_laghi_rows,
            )
            sorter = (
                SpatialSorter(DEFAULT_LANDMARK_KEYWORDS) if options.enable_spatial_sort else None
            )

            result = MergeParcelsUseCase(primary_reader, supplementary_reader, sorter).execute(
                on_progress=self._on_merge_progress, is_cancelled=lambda: self._cancel_requested
            )
            for warning in result.warnings:
                self._push_event("onLogMessage", {"level": "WARNING", "message": warning})

            society_name = read_first_field_value(primary_slot.file_path, primary_config, "الجمعيه")
            filename = build_output_filename(society_name)

            self._output_dir.mkdir(parents=True, exist_ok=True)
            save_last_output_dir(self._output_dir)
            output_path = resolve_unique_path(self._output_dir / filename)
            ExportFinalFileUseCase(ProfessionalExcelWriter()).execute(
                result.parcels,
                output_path,
                on_progress=self._on_merge_progress,
                is_cancelled=lambda: self._cancel_requested,
            )
            self._last_output_path = output_path
            logger.info(f"تم حفظ الملف: {output_path}")

            self._push_event("onMergeComplete", asdict(result.stats))
        except PipelineCancelledError:
            logger.info("Pipeline cancelled by user.")
            self._push_event("onMergeFailed", {"message": "تم إلغاء العملية"})
        except Exception as exc:  # presentation boundary: never let a raw exception escape
            logger.error(f"Pipeline failed: {exc}")
            self._push_event("onMergeFailed", {"message": _GENERIC_PROCESSING_ERROR})

    def _on_merge_progress(self, percent: int, message: str) -> None:
        self._push_event("onProgressUpdate", {"percent": percent, "message": message})

    def cancel_processing(self) -> None:
        """Request cancellation of an in-progress `start_processing()` run."""
        logger.info("cancel_processing called")
        self._cancel_requested = True

    def open_search_window(self) -> None:
        """Open (or focus) the second, independent Search window."""
        logger.info("open_search_window called")
        self._open_search_window(self._last_output_path)

    def choose_output_folder(self) -> str:
        """Open a native folder picker, returning the chosen path (or '')."""
        logger.info("choose_output_folder called")
        if self._window is None:
            return ""
        result = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return ""
        self._output_dir = Path(result[0])
        save_last_output_dir(self._output_dir)
        return result[0]

    def open_output_folder(self) -> None:
        """Open the output folder in the OS file explorer."""
        logger.info("open_output_folder called")
        if self._output_dir.exists():
            os.startfile(self._output_dir)  # noqa: S606 -- Windows-only by design (project brief)

    def open_output_file(self) -> None:
        """Open the most recently generated output file directly (e.g. in Excel)."""
        logger.info("open_output_file called")
        if self._last_output_path is not None and self._last_output_path.exists():
            os.startfile(self._last_output_path)  # noqa: S606 -- Windows-only by design

    def _push_event(self, js_function: str, payload: dict[str, Any]) -> None:
        """Push data to JS by calling a `window.<js_function>(payload)`.

        `evaluate_js` must be called from the main thread's event loop
        in some pywebview backends, but on Windows/WebView2 calling it
        from a worker thread is supported, which is what background
        processing needs.
        """
        if self._window is None:
            return
        self._window.evaluate_js(f"window.{js_function}({json.dumps(payload)})")
