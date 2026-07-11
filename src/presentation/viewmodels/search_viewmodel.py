"""Search window view-model: binds the GUI to SearchHoldingsUseCase.

Loads an output file once into memory and keeps it cached (never
re-reads on every keystroke — per §8.1's performance rule) and drives
search/selection state.
"""

from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, Signal

from src.application.dto.search_result import SearchMatch
from src.application.ports.output_file_source_port import OutputFileSourcePort
from src.application.use_cases.search_holdings_use_case import SearchHoldingsUseCase
from src.domain.entities.parcel import Parcel
from src.infrastructure.excel.output_file_reader import OutputFileFormatError, OutputFileReader
from src.presentation.i18n.ar import (
    FILE_LOADED_MESSAGE,
    GENERIC_FILE_READ_ERROR,
    MALFORMED_OUTPUT_FILE_ERROR,
)


class SearchViewModel(QObject):
    """Holds the loaded dataset and drives search/selection/navigation."""

    matches_changed = Signal(list)  # list[SearchMatch]
    parcel_selected = Signal(object)  # Parcel
    parcels_available = Signal(list)  # list[Parcel] -- sub-picker for one holding ID
    load_error = Signal(str)
    file_loaded = Signal(str, int)  # path, parcel count

    def __init__(self, reader: OutputFileSourcePort | None = None) -> None:
        super().__init__()
        self._reader = reader or OutputFileReader()
        self._search_use_case = SearchHoldingsUseCase()
        self._parcels: list[Parcel] = []

    @property
    def is_loaded(self) -> bool:
        """True once a dataset has been successfully loaded."""
        return bool(self._parcels)

    def load_file(self, path: Path) -> None:
        """Load `path` into memory, replacing any previously loaded dataset.

        Emits `load_error` (a friendly Arabic message) on any failure,
        or `file_loaded` on success. Never lets a raw exception escape.
        """
        try:
            parcels = self._reader.read(path)
        except OutputFileFormatError as exc:
            logger.warning(f"Output file missing columns: {exc.missing_headers}")
            self.load_error.emit(
                MALFORMED_OUTPUT_FILE_ERROR.format(columns="، ".join(exc.missing_headers))
            )
            return
        except Exception as exc:  # presentation boundary: never let a raw exception escape
            logger.error(f"Failed to read output file: {exc}")
            self.load_error.emit(GENERIC_FILE_READ_ERROR)
            return

        self._parcels = parcels
        self.file_loaded.emit(str(path), len(parcels))

    def search(self, query: str) -> None:
        """Search the loaded dataset and emit `matches_changed`."""
        matches = self._search_use_case.execute(self._parcels, query)
        self.matches_changed.emit(matches)

    def select_match(self, match: SearchMatch) -> None:
        """Select a `SearchMatch`, resolving straight to detail or a sub-picker."""
        if len(match.parcels) == 1:
            self.parcel_selected.emit(match.parcels[0])
        else:
            self.parcels_available.emit(match.parcels)

    def select_parcel(self, parcel: Parcel) -> None:
        """Select a specific parcel directly (e.g. from a sub-picker)."""
        self.parcel_selected.emit(parcel)

    def navigate_to_neighbor(self, border_text: str) -> None:
        """Jump to the parcel whose holder name best matches `border_text`.

        A no-op if `border_text` is a fixed landmark or no holder in
        the dataset matches it closely enough.
        """
        neighbor = self._search_use_case.find_best_name_match(self._parcels, border_text)
        if neighbor is not None:
            self.parcel_selected.emit(neighbor)

    def file_loaded_message(self, count: int) -> str:
        """Return the Arabic status text for a successful load of `count` rows."""
        return FILE_LOADED_MESSAGE.format(count=count)
