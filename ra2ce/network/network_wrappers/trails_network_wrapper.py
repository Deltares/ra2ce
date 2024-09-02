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

import geopandas as gpd
from geopandas import GeoDataFrame
from networkx import MultiGraph

from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.networks_utils import graph_from_gdf
from ra2ce.network.segmentation import Segmentation


class TrailsNetworkWrapper(NetworkWrapperProtocol):
    def __init__(self, config_data: NetworkConfigData) -> None:
        logging.info(
            """The original OSM PBF import is no longer supported. 
                Instead, the beta version of package TRAILS is used. 
                First stable release of TRAILS is expected in 2023."""
        )
        self.primary_files = config_data.network.primary_file
        self.segmentation_length = config_data.cleanup.segmentation_length
        self.crs = config_data.crs

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        """Creates a network which has been prepared in the TRAILS package

        #Todo: we might later simply import the whole trails code as a package, and directly use these functions
        #Todo: because TRAILS is still in beta version we better wait with that untill the first stable version is
        # released

        Returns:
            graph_simple (NetworkX graph): Simplified graph (for use in the losses analyses).
            complex_edges (GeoDataFrame): Complex graph (for use in the damages analyses).
        """
        logging.info(
            "TRAILS importer: Reads the provided primary edge file: {}, assumes there also is a_nodes file".format(
                self.primary_files
            )
        )

        logging.warning(
            "Any coordinate projection information in the feather file will be overwritten (with default WGS84)"
        )
        # Make a pyproj CRS from the EPSG code

        _edge_file = self.primary_files[0]
        edges = gpd.read_feather(_edge_file)
        edges = edges.set_crs(self.crs)

        corresponding_node_file = _edge_file.replace("edges", "nodes")
        if not corresponding_node_file.exists():
            raise FileNotFoundError(
                "The node file could not be found while importing from TRAILS"
            )

        nodes = gpd.read_feather(corresponding_node_file)
        nodes = nodes.set_crs(self.crs)

        logging.info("TRAILS importer: start generating graph")
        # tempfix to rename columns
        edges = edges.rename({"from_id": "node_A", "to_id": "node_B"}, axis="columns")
        node_id = "id"
        graph_simple = graph_from_gdf(edges, nodes, name="network", node_id=node_id)

        logging.info("TRAILS importer: graph generating was succesfull.")
        logging.warning(
            "RA2CE will not clean-up your graph, assuming that it is already done in TRAILS"
        )

        # Segment the complex graph
        edges_complex = Segmentation.segment_graph(
            self.segmentation_length, self.crs, edges, export_link_table=False
        )

        graph_complex = graph_simple  # NOTE THAT DIFFERENCE
        # BETWEEN SIMPLE AND COMPLEX DOES NOT EXIST WHEN IMPORTING WITH TRAILS

        # Todo: better control over metadata in trails
        # Todo: better control over where things are saved in the pipeline
        return graph_complex, edges_complex
