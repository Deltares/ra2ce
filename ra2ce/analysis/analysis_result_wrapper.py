from dataclasses import dataclass
import geopandas as gpd
from ra2ce.analysis.analysis_protocol import AnalysisProtocol


@dataclass
class AnalysisResultWrapper:
    analysis_result: gpd.GeoDataFrame
    analysis: AnalysisProtocol

    def is_valid_result(self) -> bool:
        """
        Validates whether the `analysis_result` in this wrapper is valid.

        Returns:
            bool: validity of `analysis_result`.
        """
        return (
            isinstance(self.analysis_result, gpd.GeoDataFrame)
            and not self.analysis_result.empty
        )
