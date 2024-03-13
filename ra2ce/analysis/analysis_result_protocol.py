from typing import Protocol, runtime_checkable
import geopandas as gpd


@runtime_checkable
class AnalysisResultProtocol(Protocol):

    analysis_result: gpd.GeoDataFrame

    def is_valid_result(self) -> bool:
        """
        Validates the state of this instance is as a `RA2CE` result.
        """
