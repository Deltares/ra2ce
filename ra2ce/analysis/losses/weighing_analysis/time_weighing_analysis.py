import math

import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TimeWeighingAnalysis(WeighingAnalysisProtocol):
    time_list: list
    weighing_data: dict
    default_avgspeed: float = math.inf

    def __init__(self) -> None:
        self.time_list = []

    def _calculate_time(self) -> float:
        length = self.weighing_data.get("length", 0)
        avgspeed = self.weighing_data.get("avgspeed", None)
        if not avgspeed:
            avgspeed = self.default_avgspeed
        _calculated_time = round(
            (length * 1e-3) / avgspeed,
            3,
        )  # in hours and avg speed in km/h
        self.weighing_data[WeighingEnum.TIME.config_value] = _calculated_time
        return round(_calculated_time, 3)

    def calculate_value(self) -> float:
        self.time_list.append(self._calculate_time())
        return self.time_list[-1]

    def calculate_alternative_value(self, alt_dist: float) -> float:
        avgspeed = self.weighing_data.get("avgspeed", None)
        if not avgspeed:
            avgspeed = self.default_avgspeed
        alt_time = (alt_dist * 1e-3) / avgspeed  # in hours
        self.time_list.append(self._calculate_time())
        return alt_time

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        if isinstance(gdf_graph, gpd.GeoDataFrame):
            gdf_graph[WeighingEnum.TIME.config_value] = self.time_list
        elif isinstance(gdf_graph, dict):
            gdf_graph[WeighingEnum.TIME.config_value] = [self.time_list[-1]]
