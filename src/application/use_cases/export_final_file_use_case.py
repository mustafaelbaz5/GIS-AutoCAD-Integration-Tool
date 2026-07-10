"""Use case: export the final parcel list to an output file."""

from collections.abc import Sequence
from pathlib import Path

from src.application.ports.data_sink_port import DataSinkPort
from src.domain.entities.parcel import Parcel


class ExportFinalFileUseCase:
    """Writes the final, merged parcel list via a `DataSinkPort`."""

    def __init__(self, sink: DataSinkPort) -> None:
        self._sink = sink

    def execute(self, parcels: Sequence[Parcel], output_path: Path) -> None:
        """Write `parcels` to `output_path` through the injected sink."""
        self._sink.write(parcels, output_path)
