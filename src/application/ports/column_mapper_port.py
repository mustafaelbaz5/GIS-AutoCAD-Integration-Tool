"""Port for mapping a raw source row into a `ParcelRecord`."""

from abc import ABC, abstractmethod
from typing import Any

from src.application.dto.parcel_record import ParcelRecord


class ColumnMapperPort(ABC):
    """Abstract translator from a raw row to a `ParcelRecord`.

    Used by variable-schema source readers (e.g. the secondary file
    reader) so that column letters/names are never hard-coded in
    Python — the concrete implementation reads them from a YAML mapping
    at the infrastructure layer.
    """

    @abstractmethod
    def map(self, raw_row: dict[str, Any]) -> ParcelRecord:
        """Map a raw row (column key/letter -> cell value) to a ParcelRecord."""
        raise NotImplementedError
