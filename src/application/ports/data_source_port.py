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
