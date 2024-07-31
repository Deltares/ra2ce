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
import logging
import math
from typing import Protocol, runtime_checkable, Union, Optional

from geopandas import GeoDataFrame
from networkx import MultiGraph

from ra2ce.network.segmentation import Segmentation


@runtime_checkable
class NetworkWrapperProtocol(Protocol):
    def segment_graph(
        self,
        edges: GeoDataFrame,
        export_link_table: bool,
        link_tables: Optional[tuple] = None,
    ) -> Union[GeoDataFrame, tuple[GeoDataFrame, tuple]]:
        """
        Segments a complex graph based on the given segmentation length.

        Args:
        - segmentation_length (Optional[float]): The length to segment the graph edges. If None, no segmentation is applied.
        - edges_complex (gpd.GeoDataFrame): The GeoDataFrame containing the complex graph edges.
        - crs (str): The coordinate reference system to apply if the CRS is missing after segmentation.

        Returns:
        - gpd.GeoDataFrame: The segmented edges_complex GeoDataFrame.
        """
        if not math.isnan(self.segmentation_length):
            segmentation = Segmentation(edges, self.segmentation_length)
            segmented_edges = segmentation.apply_segmentation()
            if segmented_edges.crs is None:  # The CRS might have disappeared.
                segmented_edges.crs = self.crs  # set the right CRS

            if export_link_table:
                updated_link_tables = segmentation.generate_link_tables()
                segmented_edges.drop(columns=["rfid_c"], inplace=True)
                segmented_edges.rename(columns={"splt_id": "rfid_c"}, inplace=True)
                return segmented_edges, updated_link_tables
            return segmented_edges
        elif export_link_table and link_tables:
            return edges, link_tables
        elif export_link_table and not link_tables:
            logging.warning("empty link_tables is passed")
            return edges, tuple()
        else:
            return edges

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets a network built within this wrapper instance. No arguments are accepted, the `__init__` method is meant to assign all required attributes for a wrapper.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Tuple of MultiGraph representing the graph and GeoDataFrame representing the network.
        """
        pass
