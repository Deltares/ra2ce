"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from dataclasses import dataclass, field
from geopandas import GeoDataFrame, read_file, sjoin
from networkx import Graph
from numpy import nanmean
from ra2ce.graph.hazard.hazard_intersect.hazard_intersect_builder_base import (
    HazardIntersectBuilderBase,
)


@dataclass
class HazardIntersectBuilderForShp(HazardIntersectBuilderBase):
    hazard_field_name: str = ""
    hazard_aggregate_wl: str = ""
    hazard_names: list[str] = field(default_factory=list)
    ra2ce_names: list[str] = field(default_factory=list)
    hazard_shp_files: list[str] = field(default_factory=list)

    def _from_networkx(self, hazard_overlay: Graph) -> Graph:
        """Overlays the hazard shapefile over the road segments NetworkX graph.

        Args:
            hazard_overlay (NetworkX graph): The graph that should be overlayed with the hazard shapefile(s)

        Returns:
            hazard_overlay (NetworkX graph): The graph with hazard shapefile(s) data joined
        """
        # TODO check if the CRS of the graph and shapefile match

        hfns = self.hazard_field_name

        for i, (hn, rn, hfn) in enumerate(
            zip(self.hazard_names, self.ra2ce_names, hfns)
        ):
            gdf = read_file(str(self.hazard_shp_files[i]))
            spatial_index = gdf.sindex

            for u, v, k, edata in hazard_overlay.edges.data(keys=True):
                if "geometry" in edata:
                    possible_matches_index = list(
                        spatial_index.intersection(edata["geometry"].bounds)
                    )
                    possible_matches = gdf.iloc[possible_matches_index]
                    precise_matches = possible_matches[
                        possible_matches.intersects(edata["geometry"])
                    ]

                    if not precise_matches.empty:
                        if self.hazard_aggregate_wl == "max":
                            hazard_overlay[u][v][k][
                                rn + "_" + self.hazard_aggregate_wl[:2]
                            ] = precise_matches[hfn].max()
                        if self.hazard_aggregate_wl == "min":
                            hazard_overlay[u][v][k][
                                rn + "_" + self.hazard_aggregate_wl[:2]
                            ] = precise_matches[hfn].min()
                        if self.hazard_aggregate_wl == "mean":
                            hazard_overlay[u][v][k][
                                rn + "_" + self.hazard_aggregate_wl[:2]
                            ] = nanmean(precise_matches[hfn])
                    else:
                        hazard_overlay[u][v][k][
                            rn + "_" + self.hazard_aggregate_wl[:2]
                        ] = 0
                else:
                    hazard_overlay[u][v][k][rn + "_" + self.hazard_aggregate_wl[:2]] = 0

        return hazard_overlay

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame) -> GeoDataFrame:
        """Overlays the hazard shapefile over the road segments GeoDataFrame. The gdf is reprojected to the hazard shapefile if necessary.

        Args:
            hazard_overlay (GeoDataFrame): the network geodataframe that should be overlayed with the hazard shapefile(s)

        Returns:
            hazard_overlay (GeoDataFrame): the network geodataframe with hazard shapefile(s) data joined
        """
        gdf_crs_original = hazard_overlay.crs

        for i, (hn, rn, hfn) in enumerate(
            zip(self.hazard_names, self.ra2ce_names, self.hazard_field_name)
        ):
            gdf_hazard = read_file(str(self.hazard_shp_files[i]))

            if hazard_overlay.crs != gdf_hazard.crs:
                hazard_overlay = hazard_overlay.to_crs(gdf_hazard.crs)

            hazard_overlay = sjoin(
                hazard_overlay, gdf_hazard[[hfn, "geometry"]], how="left"
            )
            hazard_overlay.rename(
                columns={hfn: rn + "_" + self.hazard_aggregate_wl[:2]}, inplace=True
            )

        if hazard_overlay.crs != gdf_crs_original:
            hazard_overlay = hazard_overlay.to_crs(gdf_crs_original)

        return hazard_overlay
