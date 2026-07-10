"""Port for writing merged parcels to an output destination."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from src.domain.entities.parcel import Parcel


class DataSinkPort(ABC):
    """Abstract destination for the final, merged parcel list.

    Concrete adapters (e.g. the professional Excel writer) implement
    this in the infrastructure layer.
    """

    @abstractmethod
    def write(self, parcels: Sequence[Parcel], output_path: Path) -> None:
        """Write `parcels` to `output_path`."""
        raise NotImplementedError
