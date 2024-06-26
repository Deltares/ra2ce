from typing import Any

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class LengthWeighingAnalysis(WeighingAnalysisProtocol):
    edge_data: dict[str, Any]

    def __init__(self) -> None:
        self.edge_data = {}

    def _calculate_distance(self, time: float) -> float:
        _avgspeed = self.edge_data.get("avgspeed", None)  # km/h
        return round(time * _avgspeed * 1e3, 1)  # m

    def get_current_value(self) -> float:
        _dist = self.edge_data.get(WeighingEnum.LENGTH.config_value, None)  # h
        if _dist:
            return round(_dist, 1)
        _time = self.edge_data.get(WeighingEnum.TIME.config_value, 0)  # m
        _dist = self._calculate_distance(_time)
        self.edge_data[WeighingEnum.LENGTH.config_value] = _dist
        return _dist
