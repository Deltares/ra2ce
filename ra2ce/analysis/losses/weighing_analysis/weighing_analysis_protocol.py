from typing import Any, Protocol, runtime_checkable

import geopandas as gpd


@runtime_checkable
class WeighingAnalysisProtocol(Protocol):
    edge_data: dict[str, Any]

    def get_current_value(self) -> float:
        """
        Gets the current distance/time of the edge.
        If the edge has not time attribute, it is calculated and added to the edge.

        Returns:
            float: Current distance/time value.
        """

    def calculate_alternative_value(self, alt_dist: float) -> float:
        """
        Calculates the alternative distances/times of the edge.

        Args:
            alt_dist (float): Provided alternative distance/time.

        Returns:
            float: Corrected alternative distance/time value.
        """

    def extend_graph(self, gdf_graph: gpd.GeoDataFrame | dict) -> None:
        """
        Extends the provided graph with custom attributes.
        """
