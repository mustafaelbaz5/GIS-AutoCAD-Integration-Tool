"""Port for reading a previously generated output file (Hexagonal).

Distinct from `DataSourcePort` (which reads raw, pre-merge sources):
this reads the *final* merged output back into `Parcel` entities, for
the Search feature (Iteration 2 Task C).
"""

from abc import ABC, abstractmethod
from pathlib import Path

from src.domain.entities.parcel import Parcel


class OutputFileSourcePort(ABC):
    """Abstract source of parcels from a previously generated output file."""

    @abstractmethod
    def read(self, path: Path) -> list[Parcel]:
        """Read and return all parcels from the output file at `path`."""
        raise NotImplementedError
