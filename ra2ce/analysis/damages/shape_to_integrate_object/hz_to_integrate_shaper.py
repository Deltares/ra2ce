import geopandas as gpd

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class HzToIntegrateShaper(ToIntegrateShaperProtocol):
    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        self.gdf = gdf

    def get_return_periods(self) -> list:
        return sorted(c for c in self.gdf.columns if c.startswith("dam"))

    def shape_to_integrate_object(
        self, return_periods: list
    ) -> dict[str : gpd.GeoDataFrame]:
        _to_integrate = self.gdf[return_periods]

        _to_integrate.columns = [
            float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
        ]
        return {
            DamageCurveEnum.HZ.name: _to_integrate.sort_index(
                axis="columns", ascending=False
            )
        }
