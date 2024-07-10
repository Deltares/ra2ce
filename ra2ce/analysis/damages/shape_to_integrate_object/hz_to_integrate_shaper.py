import geopandas as gpd

from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class HzToIntegrateShaper(ToIntegrateShaperProtocol):
    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        self.gdf = gdf

    def get_damage_columns(self) -> list:
        return [c for c in self.gdf.columns if c.startswith("dam")]

    def shape_to_integrate_object(self, damage_columns: list) -> list[gpd.GeoDataFrame]:
        _to_integrate = self.gdf[damage_columns]

        _to_integrate.columns = [
            float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
        ]
        return [_to_integrate.sort_index(axis="columns", ascending=False)]
