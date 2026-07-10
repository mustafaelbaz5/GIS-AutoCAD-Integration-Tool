"""Area value object (فدان / قيراط / سهم)."""

from dataclasses import dataclass

from src.domain.exceptions import InvalidAreaError


@dataclass(frozen=True)
class Area:
    """Raw area components in traditional Egyptian agricultural units.

    Holds only the source values; conversion to square meters is a
    separate concern handled by
    :class:`src.domain.services.area_calculator.AreaCalculator`, keeping
    this value object free of calculation logic.
    """

    feddan: float | None
    qirat: float | None
    sahm: float | None

    def __post_init__(self) -> None:
        for name, component in (
            ("feddan", self.feddan),
            ("qirat", self.qirat),
            ("sahm", self.sahm),
        ):
            if component is not None and component < 0:
                raise InvalidAreaError(f"{name} must not be negative, got {component}")

    @property
    def is_empty(self) -> bool:
        """True when all three components are absent."""
        return self.feddan is None and self.qirat is None and self.sahm is None
