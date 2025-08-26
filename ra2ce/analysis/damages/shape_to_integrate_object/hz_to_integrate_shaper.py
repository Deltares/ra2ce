import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class HzToIntegrateShaper(ToIntegrateShaperProtocol):
    """
    Shapes hazard data for integration.

    Attributes:
        gdf (GeoDataFrame): Input GeoDataFrame containing hazard data.
    """
    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        """
        Initialize the shaper with a GeoDataFrame.

        Args:
            gdf: GeoDataFrame containing hazard data.
        """
        self.gdf = gdf

    def get_return_periods(self) -> list:
        """
        Get the return periods available in the GeoDataFrame.

        Returns:
            list[float]: Sorted list of return periods extracted from the columns.
        """
        return sorted(c for c in self.gdf.columns if c.startswith("dam"))

    def shape_to_integrate_object(
        self, return_periods: list
    ) -> dict[str : gpd.GeoDataFrame]:
        """
        Shape the hazard data for integration based on selected return periods.

        Args:
            return_periods: List of return period column names to extract.

        Returns:
            dict[str, GeoDataFrame]: Dictionary mapping the damage curve name to
            a GeoDataFrame containing the selected and sorted hazard data.
        """
        _to_integrate = self.gdf[return_periods]

        _to_integrate.columns = [
            float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
        ]
        return {
            DamageCurveEnum.HZ.name: _to_integrate.sort_index(
                axis="columns", ascending=False
            )
        }
