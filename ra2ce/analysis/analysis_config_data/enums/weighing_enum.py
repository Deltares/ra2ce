from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class WeighingEnum(Ra2ceEnumBase):
    NONE = 0
    LENGTH = 1
    TIME = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> WeighingEnum:
        return WeighingEnum(super().get_enum(input_str))
