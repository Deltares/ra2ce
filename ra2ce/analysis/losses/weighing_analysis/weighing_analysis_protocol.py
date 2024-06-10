from typing import Protocol, runtime_checkable

import geopandas as gpd


@runtime_checkable
class WeighingAnalysisProtocol(Protocol):
    weighing_data: dict

    def calculate_value(self) -> float:
        """
        Calculates the distance/time of the current `weighing_data` collection.

        Returns:
            float: Single distance/time value.
        """

    def calculate_alternative_value(self, alt_dist: float) -> float:
        """
        Calculates alternative distances/times relative the current `weighing_data` collection.

        Args:
            alt_dist (float): Provided alternative distance/time.

        Returns:
            float: Corrected alternative distance/time value.
        """

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        """
        Extends the provided graph with custom attributes.
        """
