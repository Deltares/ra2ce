from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AnalysisDamagesEnum(Ra2ceEnumBase):
    DAMAGES = 1
    DAMAGES_WITH_ASSETS = 2 # refers o the mode in which damage will be estimated for the standard cross-sections and
    # specific assets (Bridge, viaducts, and tunnels for now)
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> AnalysisDamagesEnum:
        return AnalysisDamagesEnum(super().get_enum(input_str))
