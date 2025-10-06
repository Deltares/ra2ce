from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AnalysisEnum(Ra2ceEnumBase):
    ADAPTATION = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> AnalysisEnum:
        return AnalysisEnum(super().get_enum(input_str))
