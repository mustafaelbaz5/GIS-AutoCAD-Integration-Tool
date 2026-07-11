"""Port for reading parcel data from a source (Hexagonal architecture)."""

from abc import ABC, abstractmethod

from src.application.dto.parcel_record import ParcelRecord


class DataSourcePort(ABC):
    """Abstract source of `ParcelRecord`s.

    Concrete adapters (e.g. Excel readers) implement this in the
    infrastructure layer. The application layer depends only on this
    abstraction, never on a concrete reader.
    """

    @abstractmethod
    def read(self) -> list[ParcelRecord]:
        """Read and return all parcel records from this source."""
        raise NotImplementedError

    @property
    def excluded_count(self) -> int:
        """Rows filtered out by this source's own exclusion rule, if any.

        Defaults to 0 so most sources need no changes; sources with an
        exclusion rule (e.g. the secondary reader's لاغى filter)
        override this to report how many rows `read()` last dropped.
        """
        return 0

    @property
    def sheet_fallback_warning(self) -> str | None:
        """Set when `read()` had to fall back to a different sheet than configured.

        None by default. Sources that can hit this (e.g. an Excel reader
        whose configured sheet name isn't present in the workbook)
        override this to report what happened, so the caller can surface
        it to the user instead of silently reading from an unexpected sheet.
        """
        return None
