from typing import Any

import geopandas as gpd

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

    def calculate_alternative_value(self, alt_dist: float) -> float:
        return self._calculate_time(alt_dist)

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        if isinstance(gdf_graph, gpd.GeoDataFrame):
            gdf_graph[WeighingEnum.TIME.config_value] = self.time_list
        elif isinstance(gdf_graph, dict):
            gdf_graph[WeighingEnum.TIME.config_value] = [self.time_list[-1]]
