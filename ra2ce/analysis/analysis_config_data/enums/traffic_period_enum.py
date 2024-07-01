from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class TrafficPeriodEnum(Ra2ceEnumBase):
    NONE = 0
    DAY = 1
    EVENING = 2
    OTHER = 9
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> TrafficPeriodEnum:
        return super().get_enum(input)
