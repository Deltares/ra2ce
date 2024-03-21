import geopandas as gpd
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.indirect.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TimeWeighingAnalysis(WeighingAnalysisProtocol):
    time_list: list
    weighing_data: dict

    def __init__(self) -> None:
        self.time_list = []

    def _calculate_time(self) -> float:
        _calculated_time = round(
            (self.weighing_data["length"] * 1e-3) / self.weighing_data["avgspeed"],
            2,
        )  # in hours and avg speed in km/h
        self.weighing_data[WeighingEnum.TIME.config_value] = _calculated_time
        return round(_calculated_time, 2)

    def calculate_distance(self) -> float:
        self.time_list.append(self._calculate_time())
        return self.time_list[-1]

    def calculate_alternative_distance(self, alt_dist: float) -> float:
        alt_time = (alt_dist * 1e-3) / self.weighing_data["avgspeed"]  # in hours
        self.time_list.append(self._calculate_time())
        return alt_time

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        gdf_graph[WeighingEnum.TIME.config_value] = self.time_list
