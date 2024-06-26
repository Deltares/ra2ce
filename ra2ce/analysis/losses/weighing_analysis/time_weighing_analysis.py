from typing import Any

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TimeWeighingAnalysis(WeighingAnalysisProtocol):
    time_list: list
    edge_data: dict[str, Any]

    def __init__(self) -> None:
        self.time_list = []
        self.edge_data = {}

    def _calculate_time(self, dist: float) -> float:
        _avgspeed = self.edge_data.get("avgspeed", None)  # km/h
        return round(dist * 1e-3 / _avgspeed, 3)  # h

    def get_current_value(self) -> float:
        _time = self.edge_data.get(WeighingEnum.TIME.config_value, None)  # h
        if not _time:
            _dist = self.edge_data.get(WeighingEnum.LENGTH.config_value, 0)  # m
            _time = self._calculate_time(_dist)
            self.edge_data[WeighingEnum.TIME.config_value] = _time
        self.time_list.append(_time)
        return _time
