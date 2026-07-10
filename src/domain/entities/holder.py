"""Land holder entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Holder:
    """The person who holds a land parcel."""

    name: str | None
    """اسم الحائز"""

    national_id: str | None
    """الرقم القومي — sourced exclusively from the secondary file."""
