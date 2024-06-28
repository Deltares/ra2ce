from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class PartOfDayEnum(Ra2ceEnumBase):
    DAY = 1
    EVENING = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> PartOfDayEnum:
        return super().get_enum(input)
