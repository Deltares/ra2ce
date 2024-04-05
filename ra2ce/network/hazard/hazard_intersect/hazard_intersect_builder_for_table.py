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

from dataclasses import dataclass

from geopandas import GeoDataFrame
from networkx import Graph
from pandas import read_csv

from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_base import (
    HazardIntersectBuilderBase,
)
from ra2ce.network.networks_utils import graph_from_gdf, graph_to_gdf


@dataclass
class HazardIntersectBuilderForTable(HazardIntersectBuilderBase):
    hazard_field_name: str = ""
    network_file_id: str = ""
    hazard_id: str = ""
    ra2ce_name_key: str = "RA2CE name"

    def _from_network_x(self, hazard_overlay: Graph) -> Graph:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        gdf, gdf_nodes = graph_to_gdf(hazard_overlay, save_nodes=True)
        gdf = self._from_geodataframe(gdf)

        # TODO: Check if the graph is created again correctly.
        hazard_overlay = graph_from_gdf(gdf, gdf_nodes)
        return hazard_overlay

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        for haz in self.hazard_files.table:
            if haz.suffix in [".csv"]:
                hazard_overlay = self._join_table(hazard_overlay, haz)
        return hazard_overlay

    def _join_table(self, graph: Graph, hazard: str) -> Graph:
        df = read_csv(hazard)
        df = df[self.hazard_field_name]
        graph = graph.merge(
            df,
            how="left",
            left_on=self.network_file_id,
            right_on=self.hazard_id,
        )

        graph.rename(
            columns={
                self.hazard_field_name: [
                    n[:-3] for n in self.hazard_name_table[self.ra2ce_name_key]
                ][0]
            },
            inplace=True,
        )  # Check if this is the right name
        return graph
