import math
from typing import Any

import geopandas as gpd

from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class LengthWeighingAnalysis(WeighingAnalysisProtocol):
    weighing_data: dict[str, Any]
    avgspeed_dict: dict[str, float]

    def __init__(self) -> None:
        pass

    def calculate_value(self) -> float:
        return math.nan

    def calculate_alternative_value(self, alt_dist: float) -> float:
        return alt_dist

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        return
