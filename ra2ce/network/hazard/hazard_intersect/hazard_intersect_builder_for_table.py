"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023-2026 Stichting Deltares

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
from pathlib import Path

from geopandas import GeoDataFrame
from networkx import Graph
from pandas import DataFrame, read_csv

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
    table_files: list[Path] = field(default_factory=list)
    hazard_name_table: DataFrame = field(default_factory=DataFrame)

    def _from_networkx(self, hazard_overlay: Graph) -> Graph:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        gdf, gdf_nodes = graph_to_gdf(hazard_overlay, save_nodes=True)
        gdf = self._from_geodataframe(gdf)

        # node_A/node_B may be stored as lists (e.g. in simplified/merged graphs);
        # graph_from_gdf requires hashable scalars as node identifiers.
        for _col in ["node_A", "node_B"]:
            if _col in gdf.columns:
                gdf[_col] = gdf[_col].apply(
                    lambda x: x[0] if isinstance(x, list) else x
                )

        # TODO: Check if the graph is created again correctly.
        hazard_overlay = graph_from_gdf(gdf, gdf_nodes, node_id="node_fid")
        return hazard_overlay

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        for haz in self.table_files:
            if haz.suffix in [".csv"]:
                hazard_overlay = self._join_table(hazard_overlay, haz)
        return hazard_overlay

    def _join_table(self, graph: Graph, hazard: str) -> Graph:
        df = read_csv(hazard)
        self.network_file_id = 'rfid_c'
        df = df[[self.hazard_field_name, self.hazard_id]]
        df = df.drop_duplicates(subset=self.hazard_id)

        ra2ce_col = [
            n[:-3] for n in self.hazard_name_table[self.ra2ce_name_key]
        ][0] + "_ma"

        # rfid_c may be a list of IDs (simplified edges covering multiple complex edges).
        # Explode so each ID gets its own row, merge, then aggregate back per original row
        # so the graph length is preserved.
        _orig_index = graph.index
        graph = graph.reset_index(drop=True)

        exploded = graph[[self.network_file_id]].copy()
        exploded["_orig_idx"] = exploded.index
        exploded = exploded.explode(self.network_file_id)
        exploded[self.network_file_id] = exploded[self.network_file_id].astype(
            df[self.hazard_id].dtype
        )

        merged = exploded.merge(
            df,
            how="left",
            left_on=self.network_file_id,
            right_on=self.hazard_id,
        )

        # Aggregate: take first non-null hazard value per original row
        hazard_per_row = (
            merged.groupby("_orig_idx")[self.hazard_field_name]
            .first()
            .rename(ra2ce_col)
        )

        graph = graph.join(hazard_per_row)

        _base_col = ra2ce_col[:-3]  # e.g. "EV1"
        graph[_base_col + "_me"] = graph[ra2ce_col]
        graph[_base_col + "_fr"] = 1

        graph.index = _orig_index
        return graph
