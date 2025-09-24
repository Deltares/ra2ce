from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class EventTypeEnum(Ra2ceEnumBase):
    NONE = 0
    EVENT = 1
    RETURN_PERIOD = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> EventTypeEnum:
        return EventTypeEnum(super().get_enum(input_str))
