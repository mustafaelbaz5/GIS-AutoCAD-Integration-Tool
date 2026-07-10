"""Domain-level exceptions.

Raised by entities, value objects, and domain services. Carry no
infrastructure concerns (no Excel/GUI references) so they can be caught
uniformly by outer layers.
"""


class DomainError(Exception):
    """Base class for all domain-layer errors."""


class InvalidHoldingIdError(DomainError):
    """Raised when a holding ID value fails validation."""


class InvalidAreaError(DomainError):
    """Raised when an area component (feddan/qirat/sahm) is invalid."""
