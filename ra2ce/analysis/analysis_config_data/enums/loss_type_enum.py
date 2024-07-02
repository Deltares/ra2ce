from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class LossTypeEnum(Ra2ceEnumBase):
    NONE = 0
    UNIFORM = 1
    CATEGORIZED = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> LossTypeEnum:
        return super().get_enum(input)
