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

from collections import defaultdict
from dataclasses import dataclass

import geopandas as gpd
import networkx as nx
from geopandas import GeoDataFrame
from numpy import int64 as npInt64
from shapely.geometry import LineString, Point
from snkit.network import Network as SnkitNetwork

from ra2ce.network import add_x_y_to_nodes

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


@dataclass(kw_only=True)
class NxToSnkitNetworkConverter:
    """
    Class responsible to convert a `networkx.MultiGraph` into
    a matching `snkit.network.Network`.
    """

    networkx_graph: NxGraph
    node_id_column_name: str = "id"
    edge_from_id_column_name: str = "from_id"
    edge_to_id_column_name: str = "to_id"

    def convert(self) -> SnkitNetwork:
        """
        Converts a regular `NetworkX.graph` into a `snkit.network.Network` object.

        Returns:
            SnkitNetwork: The resulting `snkit.network.Network` converted object.
        """
        # Extract graph values
        _crs = self.networkx_graph.graph.get("crs", None)
        # add x and y to the nodes of a graph
        self.networkx_graph = add_x_y_to_nodes(self.networkx_graph)

        # Create new network
        snkit_network = SnkitNetwork()
        node_attributes = [
            {self.node_id_column_name: node, **data}
            for node, data in self.networkx_graph.nodes(data=True)
        ]
        snkit_network.nodes = GeoDataFrame(node_attributes)
        snkit_network.nodes = self._check_and_create_node_geometries(
            snkit_network.nodes
        )
        snkit_network.nodes.set_geometry("geometry", inplace=True, crs=_crs)

        edge_attributes = [
            {self.edge_from_id_column_name: u, self.edge_to_id_column_name: v, **data}
            for u, v, data in self.networkx_graph.edges(data=True)
        ]
        snkit_network.edges = GeoDataFrame(edge_attributes)
        snkit_network = self._check_and_create_edge_geometries(snkit_network)
        snkit_network.edges.set_geometry("geometry", inplace=True, crs=_crs)

        # Set network CRS to default_crs
        snkit_network.set_crs(_crs)

        # Checks
        snkit_network = self._check_edge_ids(snkit_network)
        snkit_network = self._get_nodes_degree(snkit_network)

        # Return converted and validated network
        return snkit_network

    def _check_edge_ids(self, network: SnkitNetwork) -> SnkitNetwork:
        if not id in network.edges.columns:
            network.edges["id"] = network.edges.index
        return network

    def _get_nodes_degree(self, network: SnkitNetwork) -> SnkitNetwork:
        def _calculate_degree(snkit_network: SnkitNetwork) -> dict:
            degrees = defaultdict(int)

            from_ids = snkit_network.edges["from_id"].to_numpy(dtype=npInt64)
            for from_id in from_ids:
                degrees[from_id] += 1

            to_ids = snkit_network.edges["to_id"].to_numpy(dtype=npInt64)
            for to_id in to_ids:
                degrees[to_id] += 1

            return degrees

        degrees = _calculate_degree(network)
        network.nodes["degree"] = network.nodes["id"].apply(
            lambda node_id: degrees.get(node_id, 0)
        )
        return network

    def _check_and_create_node_geometries(
        self,
        geo_dataframe: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        """
        Check if there is a geometry column in network.nodes.
        If not, check if both 'x' and 'y' columns are present.
        If both are present, create Point geometries for each row.
        If either 'x' or 'y' is missing, raise a ValueError.

        Parameters:
        gdf (snkit.network.Network): The gdf object containing nodes as a GeoDataFrame.

        Raises:
        ValueError: If neither geometry column nor both 'x' and 'y' columns are present in network.nodes.
        """
        if "geometry" in geo_dataframe.columns:
            return geo_dataframe

        if "x" in geo_dataframe.columns and "y" in geo_dataframe.columns:
            geo_dataframe["geometry"] = geo_dataframe.apply(
                lambda row: Point(row["x"], row["y"]), axis=1
            )
            return geo_dataframe
        else:
            raise ValueError(
                "The network nodes must contain either a 'geometry' column or both 'x' and 'y' columns."
            )

    def _check_and_create_edge_geometries(
        self,
        network: SnkitNetwork,
    ) -> SnkitNetwork:
        """
        Creates a GEOMETRY attribute for each edge in the graph using the geometries of the nodes.

        Parameters:
        G (nx.Graph): The NetworkX graph with nodes having geometries.

        Returns:
        nx.Graph: The NetworkX graph with edges having GEOMETRY attributes.
        """

        def create_linestring(row):
            from_geom = node_geometries.get(row["from_id"])
            to_geom = node_geometries.get(row["to_id"])
            if from_geom is None or to_geom is None:
                raise ValueError(
                    f"Geometry missing for from_id {row['from_id']} or to_id {row['to_id']}."
                )
            return LineString([from_geom, to_geom])

        if "geometry" in network.edges.columns:
            return network
        # Check if nodes have geometries
        if not ("geometry" in network.nodes.columns):
            network.nodes = self._check_and_create_node_geometries(network.nodes)

        # Convert nodes to a dictionary for fast lookup
        node_geometries = network.nodes.set_index("id")["geometry"].to_dict()

        # Apply the function to create the geometry column
        network.edges["geometry"] = network.edges.apply(create_linestring, axis=1)

        return network
