import geopandas as gpd
from typing import Any, Protocol, runtime_checkable

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum


@runtime_checkable
class ToIntegrateShaperProtocol(Protocol):
    gdf: gpd.GeoDataFrame

    def get_damage_columns(self) -> float:
        """
        Gets the columns' names that have damages calculated

        Returns:
            list: columns' name that have damages calculated.
        """

    def shape_to_integrate_object(self, damage_columns: list) -> list[gpd.GeoDataFrame]:
        """
        Gets the return periods and create columns for risk calculation for each damage curve and return period
        Returns:
            list[GeoDataFrame]:
            to_integrate objects each corresponding to each vulnerability curve to be used for risk calculation
        """
