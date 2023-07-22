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
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import networkx as nx
import osmnx
from networkx import MultiDiGraph
from shapely.geometry.base import BaseGeometry

import ra2ce.graph.networks_utils as nut


class OsmNetworkWrapper:
    network_dict: dict
    output_path: Path

    def __init__(self, config: dict) -> None:
        if not config:
            raise ValueError("Config cannot be None")
        if not config.get("network", {}):
            raise ValueError("A network dictionary is required for creating a OsmNetworkWrapper object.")
        if not isinstance(config.get("network"), dict):
            raise ValueError('Config["network"] should be a dictionary')
        self.network_dict = config["network"]
        self.output_path = config["static"] / "output_graph"

    def download_graph_from_osm(self) -> MultiDiGraph:
        if not self.network_dict["polygon"]:
            raise FileNotFoundError("No or invalid polygon file is introduced for OSM download")
        if Path(self.output_path.parent / "network" / self.network_dict["polygon"]).exists():
            polygon_file = self.output_path.parent / "network" / self.network_dict["polygon"]
        else:
            raise FileNotFoundError("No polygon_file file found")
        poly_dict = nut.read_geojson(geojson_file=polygon_file)  # It can only read in one geojson
        return self.get_graph_from_osm_download(
            polygon=nut.geojson_to_shp(poly_dict),
            network_type=self.network_dict.get("network_type", None),
            link_type=self.network_dict.get("road_type", None)
        )

    def get_graph_from_osm_download(self, polygon: BaseGeometry, link_type: str, network_type: str) -> MultiDiGraph:
        """
        Creates a network from a polygon by downloading via the OSM API in the extent of the polygon.
        Args:
            polygon: Shapely Polygon or Multipolygon geometry
            link_type: string, e.g., "highway,motorway"
            network_type: string {"all_private", "all", "bike", "drive", "drive_service", "walk"}
        Returns:
            complex_graph (NetworkX graph): Complex graph (for use in the direct analyses and
            input to derive simplified network).
        """
        if not link_type:
            # The user specified only the network type.
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type,
                simplify=False,
                retain_all=True,
            )
        elif not network_type:
            # The user specified only the road types.
            cf = f'["highway"~"{link_type.replace(",", "|")}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                custom_filter=cf,
                simplify=False,
                retain_all=True
            )
        else:
            # The user specified the network type and road types.
            cf = f'["highway"~"{link_type.replace(",", "|")}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type,
                custom_filter=cf,
                simplify=False,
                retain_all=True,
            )
        logging.info(
            "graph downloaded from OSM with {:,} nodes and {:,} edges".format(
                len(list(_complex_graph.nodes())), len(list(_complex_graph.edges()))
            )
        )
        self.get_clean_graph(_complex_graph)
        return _complex_graph

    @staticmethod
    def get_clean_graph(complex_graph):
        complex_graph = OsmNetworkWrapper.drop_duplicates(complex_graph)
        complex_graph = OsmNetworkWrapper.snap_nodes(complex_graph, 10)
        return complex_graph

    @staticmethod
    def drop_duplicates(complex_graph: MultiDiGraph) -> MultiDiGraph:
        unique_elements = set()
        unique_graph = OsmNetworkWrapper.drop_duplicates_in_nodes(
            unique_elements=unique_elements, unique_graph=None, graph=complex_graph
        )
        unique_graph = OsmNetworkWrapper.drop_duplicates_in_edges(
            unique_elements=unique_elements, unique_graph=unique_graph, graph=complex_graph
        )
        return unique_graph

    @staticmethod
    def drop_duplicates_in_nodes(unique_elements: set, unique_graph, graph: MultiDiGraph):
        if unique_graph is None:
            unique_graph = nx.MultiDiGraph()
        for node, data in graph.nodes(data=True):
            if data['x'] is None or data['y'] is None:
                raise ValueError("Incompatible coordinate keys. Check the keys which define the x and y coordinates")
            else:
                x, y = data['x'], data['y']  # Assuming 'x' and 'y' attributes store the geometry
                geometry = (x, y)
                if geometry not in unique_elements:
                    node_attributes = {
                        key: value for key, value in data.items()
                    }
                    unique_graph.add_node(node, **node_attributes)
                    unique_elements.add(geometry)
        return unique_graph

    @staticmethod
    def drop_duplicates_in_edges(unique_elements, unique_graph, graph):
        """
        checks if both extremities are in the unique_graph (u has not the same coor of v, no line from u to itself is
        allowed). Checks if an edge is already made between such extremities with the given id and coordinates before
        considering it in the unique graph
        """
        if unique_graph is None:
            raise ValueError("""
            unique_graph cannot be None. First perform the drop_duplicates_in_nodes on the graph to generate a 
            unique_graph
            """)
        for u, v, data in graph.edges(data=True):

            extremities_data = OsmNetworkWrapper.get_extremities_data_for_sub_graph(from_node_id=u, to_node_id=v,
                                                                                    sub_graph=unique_graph,
                                                                                    graph=graph,
                                                                                    shared_elements=unique_elements)
            if extremities_data.from_to_id is not None and extremities_data.from_to_coor is not None:
                if (extremities_data.from_to_id, extremities_data.to_from_id) not in unique_elements and \
                        (extremities_data.from_to_coor, extremities_data.to_from_coor) not in unique_elements:
                    edge_attributes = {
                        key: value for key, value in data.items()
                    }
                    unique_graph.add_edge(extremities_data.from_id, extremities_data.to_id, **edge_attributes)
                    unique_elements.add((extremities_data.from_to_id, extremities_data.to_from_id))
                    unique_elements.add((extremities_data.from_to_coor, extremities_data.to_from_coor))

        return unique_graph

    @staticmethod
    def get_extremities_data_for_sub_graph(from_node_id, to_node_id, sub_graph, graph, shared_elements):
        """Both extremities should be in the unique_graph still makes an edge between similar node to u (the node
        with u coordinates and different id, included in the unique_graph) and v Here, sub_graph is the unique_graph
        and graph is complex_graph Shared elements are shared btw sub_graph and graph, which are elements to include
        when dropping duplicates"""

        if from_node_id in sub_graph.nodes() and to_node_id in sub_graph.nodes():
            return ExtremitiesData.arrange_extremities_data(
                from_node_id=from_node_id, to_node_id=to_node_id, graph=sub_graph
            )
        elif (graph.nodes[from_node_id]['x'], graph.nodes[from_node_id]['y']) in shared_elements and \
                to_node_id in sub_graph.nodes():

            from_node_id_prime = OsmNetworkWrapper.find_node_id_by_coor(
                sub_graph, graph.nodes[from_node_id]['x'], graph.nodes[from_node_id]['y']
            )
            if from_node_id_prime == to_node_id:
                return ExtremitiesData()
            else:
                return ExtremitiesData.arrange_extremities_data(from_node_id=from_node_id_prime, to_node_id=to_node_id,
                                                                graph=sub_graph)

        elif from_node_id in sub_graph.nodes() and \
                (graph.nodes[to_node_id]['x'], graph.nodes[to_node_id]['y']) in shared_elements:

            to_node_id_prime = OsmNetworkWrapper.find_node_id_by_coor(
                sub_graph, graph.nodes[to_node_id]['x'], graph.nodes[to_node_id]['y']
            )
            if from_node_id == to_node_id_prime:
                return ExtremitiesData()
            else:
                return ExtremitiesData.arrange_extremities_data(from_node_id=from_node_id, to_node_id=to_node_id_prime,
                                                                graph=sub_graph)
        else:
            return ExtremitiesData()

    @staticmethod
    def find_node_id_by_coor(graph: MultiDiGraph, target_x: float, target_y: float):
        """
         finds the node in unique graph with the same coor
        """
        for node, data in graph.nodes(data=True):
            if 'x' in data and 'y' in data and data['x'] == target_x and data['y'] == target_y:
                return node
        return None

    @staticmethod
    def snap_nodes(complex_graph, threshold):

        pass


@dataclass
class ExtremitiesData:
    from_id: int = None
    to_id: int = None
    from_to_id: Union[None, tuple] = None
    to_from_id: Union[None, tuple] = None
    from_to_coor: Union[None, tuple] = None
    to_from_coor: Union[None, tuple] = None

    @staticmethod
    def arrange_extremities_data(from_node_id: int, to_node_id: int, graph: MultiDiGraph):
        return ExtremitiesData(
            from_id=from_node_id,
            to_id=to_node_id,
            from_to_id=(from_node_id, to_node_id),
            to_from_id=(to_node_id, from_node_id),
            from_to_coor=(
                (graph.nodes[from_node_id]['x'], graph.nodes[to_node_id]['x']),
                (graph.nodes[from_node_id]['y'], graph.nodes[to_node_id]['y'])
            ),
            to_from_coor=(
                (graph.nodes[to_node_id]['x'], graph.nodes[from_node_id]['x']),
                (graph.nodes[to_node_id]['y'], graph.nodes[from_node_id]['y'])
            )
        )
