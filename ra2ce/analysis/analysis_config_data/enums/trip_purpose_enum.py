from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class TripPurposeEnum(Ra2ceEnumBase):
    NONE = 0
    BUSINESS = 1
    COMMUTE = 2
    FREIGHT = 3
    OTHER = 4
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> TripPurposeEnum:
        return super().get_enum(input)
