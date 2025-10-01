from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class RiskCalculationModeEnum(Ra2ceEnumBase):
    NONE = 0
    DEFAULT = 1
    CUT_FROM_YEAR = 2
    TRIANGLE_TO_NULL_YEAR = 3
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> RiskCalculationModeEnum:
        return RiskCalculationModeEnum(super().get_enum(input_str))
