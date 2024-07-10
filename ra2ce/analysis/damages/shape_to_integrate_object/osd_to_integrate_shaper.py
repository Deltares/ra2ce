import geopandas as gpd
import re

from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class OsdToIntegrateShaper(ToIntegrateShaperProtocol):
    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        self.gdf = gdf

    def get_damage_columns(self) -> list:
        # Extract the RP values from the columns
        pattern = re.compile(r"RP(\d+)")

        rp_values = {
            pattern.search(c).group(1) for c in self.gdf.columns if pattern.search(c)
        }
        if not rp_values:
            raise ValueError("No damage column with RP found")

        return [float(rp) for rp in rp_values]

    def shape_to_integrate_object(self, damage_columns: list) -> list[gpd.GeoDataFrame]:
        _to_integrate = self.gdf[damage_columns]

        _to_integrate.columns = [
            float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
        ]
        return [_to_integrate.sort_index(axis="columns", ascending=False)]

        # _to_integrate = _to_integrate.sort_index(
        #     axis="columns", ascending=False
        # )  # from large to small RP
