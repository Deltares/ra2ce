from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AnalysisLossesEnum(Ra2ceEnumBase):
    SINGLE_LINK_REDUNDANCY = 1
    MULTI_LINK_REDUNDANCY = 2
    OPTIMAL_ROUTE_ORIGIN_DESTINATION = 3
    MULTI_LINK_ORIGIN_DESTINATION = 4
    OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION = 5
    MULTI_LINK_ORIGIN_CLOSEST_DESTINATION = 6
    SINGLE_LINK_LOSSES = 7
    MULTI_LINK_LOSSES = 8
    MULTI_LINK_ISOLATED_LOCATIONS = 9
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> AnalysisLossesEnum:
        return AnalysisLossesEnum(super().get_enum(input_str))
