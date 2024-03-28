from typing import Protocol, runtime_checkable

import geopandas as gpd


@runtime_checkable
class WeighingAnalysisProtocol(Protocol):
    weighing_data: dict

    def calculate_distance(self) -> float:
        """
        Calculates the distance of the current `weighing_data` collection.

        Returns:
            float: Single distance value.
        """

    def calculate_alternative_distance(self, alt_dist: float) -> float:
        """
        Calculates alternative distances relative the current `weighing_data` collection.

        Args:
            alt_dist (float): Provided alternative distance.

        Returns:
            float: Corrected alternative distance.
        """

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        """
        Extends the provided graph with custom attributes.
        """
