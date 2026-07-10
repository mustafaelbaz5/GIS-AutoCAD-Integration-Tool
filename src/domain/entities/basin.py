"""Basin entity (حوض)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Basin:
    """An irrigation basin that groups parcels for spatial sorting."""

    name: str | None
    """اسم الحوض"""

    code: str | None
    """كود الحوض"""
