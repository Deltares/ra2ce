from typing import Any, Protocol, runtime_checkable

import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum


@runtime_checkable
class ToIntegrateShaperProtocol(Protocol):
    """
    Protocol for shaping hazard data into objects suitable for risk integration.

    Attributes:
        gdf (GeoDataFrame): Input GeoDataFrame containing hazard data.
    """

    gdf: gpd.GeoDataFrame

    def get_return_periods(self) -> list:
        """
        Get the names of the columns containing damage data.

        Returns:
            list[float]: Column names corresponding to calculated damages.
        """

    def shape_to_integrate_object(
        self, return_periods: list
    ) -> dict[str : gpd.GeoDataFrame]:
        """
        Create objects for integration based on damage curves and return periods.

        Args:
            return_periods: List of return periods to extract and prepare.

        Returns:
            dict[str, GeoDataFrame]: A dictionary mapping each vulnerability curve
            name to a GeoDataFrame containing the relevant columns for risk calculation.
        """
