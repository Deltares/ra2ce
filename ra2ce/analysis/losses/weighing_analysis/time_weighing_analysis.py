from typing import Any

import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.networks_utils import get_avgspeed_per_road_type


class TimeWeighingAnalysis(WeighingAnalysisProtocol):
    weighing_data: dict[str, Any]
    avgspeed_dict: dict[str, float]

    def __init__(self, gdf_graph: gpd.GeoDataFrame) -> None:
        self.avgspeed_dict = {
            _road_type.config_value: get_avgspeed_per_road_type(gdf_graph, _road_type)
            for _road_type in RoadTypeEnum
        }

    def _calculate_time(self, dist: float) -> float:
        _avgspeed = self.weighing_data.get("avgspeed", None)  # km/h
        if not _avgspeed:
            _avgspeed = self.avgspeed_dict[self.weighing_data["highway"]]
        return round(
            (dist * 1e-3) / _avgspeed,
            7,
        )  # h

    def calculate_current_value(self) -> float:
        _dist = self.weighing_data.get("length", 0)  # m
        _time = self._calculate_time(_dist)
        self.weighing_data[WeighingEnum.TIME.config_value] = _time
        return _time

    def calculate_alternative_value(self, alt_dist: float) -> float:
        return self._calculate_time(alt_dist)
