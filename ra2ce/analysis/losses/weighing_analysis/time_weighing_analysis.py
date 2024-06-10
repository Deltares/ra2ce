from typing import Any

import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TimeWeighingAnalysis(WeighingAnalysisProtocol):
    time_list: list[float]
    weighing_data: dict[str, Any]
    avgspeed_dict: dict[str, float]

    def __init__(self) -> None:
        self.time_list = []

    def _calculate_time(self, dist: float) -> float:
        _avgspeed = self.weighing_data.get("avgspeed", None)  # km/h
        if not _avgspeed:
            _avgspeed = self.avgspeed_dict[self.weighing_data["highway"]]
        return round(
            (dist * 1e-3) / _avgspeed,
            7,
        )  # h

    def calculate_value(self) -> float:
        _dist = self.weighing_data.get("length", 0)  # m
        _time = self._calculate_time(_dist)
        self.weighing_data[WeighingEnum.TIME.config_value] = _time
        self.time_list.append(_time)
        return _time

    def calculate_alternative_value(self, alt_dist: float) -> float:
        return self._calculate_time(alt_dist)

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        if isinstance(gdf_graph, gpd.GeoDataFrame):
            gdf_graph[WeighingEnum.TIME.config_value] = self.time_list
        elif isinstance(gdf_graph, dict):
            gdf_graph[WeighingEnum.TIME.config_value] = [self.time_list[-1]]
