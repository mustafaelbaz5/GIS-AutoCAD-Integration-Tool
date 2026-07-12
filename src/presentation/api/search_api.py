"""Python-side bridge exposed to the search window's JavaScript.

Per Iteration 4 Task E: real fuzzy/numeric search (Iteration 2
§6.4-A), mirroring exactly what the old PySide6 `SearchViewModel` did.
No Stitch design exists for any of the 5 search screens (see
resources/design/INVENTORY.md) — the search window's HTML/CSS is
therefore plain/utilitarian, styled with the shared design tokens but
not a reproduction of a received screen. This file focuses on getting
the *behavior* right so re-styling later doesn't touch any logic here.
"""

from pathlib import Path
from typing import Any

import webview
from loguru import logger
from src.application.dto.search_result import SearchMatch
from src.application.use_cases.search_holdings_use_case import SearchHoldingsUseCase
from src.domain.entities.parcel import Parcel
from src.domain.services.area_calculator import AreaCalculator
from src.domain.value_objects.area import Area
from src.domain.value_objects.holding_id import normalize_for_join
from src.infrastructure.excel.output_file_reader import OutputFileFormatError, OutputFileReader

_MALFORMED_FILE_ERROR = "الملف غير صالح. الأعمدة الناقصة: {columns}"
_GENERIC_READ_ERROR = "تعذر قراءة الملف"


class SearchApi:
    """JS-callable API for the search window. See module docstring."""

    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._parcels: list[Parcel] = []
        self._loaded_path: Path | None = None
        self._reader = OutputFileReader()
        self._search_use_case = SearchHoldingsUseCase()

    def bind_window(self, window: webview.Window) -> None:
        """Attach the `webview.Window` this API instance belongs to."""
        self._window = window

    def load_output_file(self, path: str) -> dict[str, Any]:
        """Load `path` into memory, replacing any previously loaded dataset.

        Called either at startup (with the main window's last output
        path) or from `open_different_file` — both paths funnel
        through here, per the brief's requirement that both work.
        """
        return self._load_file(Path(path))

    def get_initial_status(self) -> dict[str, Any]:
        """Report whether a dataset is already loaded, for the window's boot state."""
        if not self._parcels:
            return {"loaded": False}
        return {"loaded": True, "count": len(self._parcels), "path": str(self._loaded_path)}

    def open_different_file(self) -> dict[str, Any]:
        """Open a native file picker and reload the in-memory dataset."""
        logger.info("open_different_file called")
        if self._window is None:
            return {"error": "Window not ready"}
        result = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            file_types=("Excel Files (*.xlsx)", "All files (*.*)"),
        )
        if not result:
            return {"cancelled": True}
        return self._load_file(Path(result[0]))

    def _load_file(self, path: Path) -> dict[str, Any]:
        try:
            parcels = self._reader.read(path)
        except OutputFileFormatError as exc:
            logger.warning(f"Output file missing columns: {exc.missing_headers}")
            return {
                "loaded": False,
                "error": _MALFORMED_FILE_ERROR.format(columns="، ".join(exc.missing_headers)),
            }
        except Exception:
            logger.exception(f"Failed to read output file: {path}")
            return {"loaded": False, "error": _GENERIC_READ_ERROR}

        self._parcels = parcels
        self._loaded_path = path
        return {"loaded": True, "count": len(parcels), "path": str(path)}

    def search_holdings(self, query: str) -> list[dict[str, Any]]:
        """Return up to 10 ranked, grouped-by-holding-ID matches for `query`."""
        matches = self._search_use_case.execute(self._parcels, query)
        return [self._serialize_match(match) for match in matches]

    def _serialize_match(self, match: SearchMatch) -> dict[str, Any]:
        return {
            "holding_id": match.holding_id,
            "holder_name": match.holder_name,
            "score": match.score,
            "parcel_count": len(match.parcels),
        }

    def get_parcels_for_holding(self, holding_id: str) -> list[dict[str, Any]]:
        """List every parcel under `holding_id`, for the multi-parcel sub-list screen."""
        group = self._group_for(holding_id)
        return [
            {
                "parcel_index": index,
                "land_number": parcel.land_number,
                "area_summary": self._area_summary(parcel.area),
            }
            for index, parcel in enumerate(group)
        ]

    def get_holding_detail(self, holding_id: str, parcel_index: int) -> dict[str, Any]:
        """Return the full record for one parcel, with per-border navigability.

        Each border includes `is_navigable` + `target_holding_id`,
        resolved server-side via the same fuzzy holder-name matching
        `SearchHoldingsUseCase` already does — JS never re-implements
        or guesses at this from the raw border text.
        """
        group = self._group_for(holding_id)
        if not group or parcel_index >= len(group):
            return {"error": "لم يتم العثور على الحيازة"}
        return self._serialize_parcel(group[parcel_index])

    def _group_for(self, holding_id: str) -> list[Parcel]:
        target = normalize_for_join(holding_id)
        return [p for p in self._parcels if normalize_for_join(str(p.holding_id)) == target]

    def _serialize_parcel(self, parcel: Parcel) -> dict[str, Any]:
        total_sqm = AreaCalculator.calculate_total_sqm(parcel.area)
        borders = {
            direction: self._serialize_border(text)
            for direction, text in (
                ("north", parcel.borders.north),
                ("south", parcel.borders.south),
                ("east", parcel.borders.east),
                ("west", parcel.borders.west),
            )
        }
        return {
            "holding_id": str(parcel.holding_id),
            "holder_name": parcel.holder.name,
            "national_id": parcel.holder.national_id,
            "basin_name": parcel.basin.name,
            "basin_code": parcel.basin.code,
            "directorate": parcel.directorate,
            "administration": parcel.administration,
            "page_number": parcel.page_number,
            "land_number": parcel.land_number,
            "feddan": parcel.area.feddan,
            "qirat": parcel.area.qirat,
            "sahm": parcel.area.sahm,
            "total_sqm": total_sqm,
            "borders": borders,
            "formatted_text": self._format_for_clipboard(parcel, total_sqm),
        }

    def _serialize_border(self, text: str | None) -> dict[str, Any]:
        neighbor = self._search_use_case.find_best_name_match(self._parcels, text) if text else None
        return {
            "text": text,
            "is_navigable": neighbor is not None,
            "target_holding_id": str(neighbor.holding_id) if neighbor else None,
        }

    def _format_for_clipboard(self, parcel: Parcel, total_sqm: float | None) -> str:
        area_line = self._area_summary(parcel.area)
        if total_sqm is not None:
            area_line += f" ≈ {total_sqm} م²"
        lines = [
            f"رقم الحيازة: {parcel.holding_id}",
            f"الحائز: {parcel.holder.name or '—'}",
            f"الرقم القومي: {parcel.holder.national_id or '—'}",
            f"الحوض: {parcel.basin.name or '—'}",
            f"رقم الأرض: {parcel.land_number or '—'}",
            f"المساحة: {area_line}",
            (
                f"الحدود: شمال({parcel.borders.north or '—'}) "
                f"جنوب({parcel.borders.south or '—'}) "
                f"شرق({parcel.borders.east or '—'}) "
                f"غرب({parcel.borders.west or '—'})"
            ),
        ]
        return "\n".join(lines)

    def _area_summary(self, area: Area) -> str:
        feddan = area.feddan or 0
        qirat = area.qirat or 0
        sahm = area.sahm or 0
        return f"{feddan:g} فدان، {qirat:g} قيراط، {sahm:g} سهم"
