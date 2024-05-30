import geopandas as gpd
import numpy as np

from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class LengthWeighingAnalysis(WeighingAnalysisProtocol):
    weighing_data: dict

    def calculate_distance(self) -> float:
        return np.nan

    def calculate_alternative_distance(self, alt_dist: float) -> float:
        return alt_dist

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        return
