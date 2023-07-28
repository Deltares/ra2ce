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
from pathlib import Path

import networkx as nx
import osmnx
from networkx import MultiDiGraph
from osmnx import consolidate_intersections
from osmnx.simplification import _is_endpoint
from osmnx_wrapper import OsmnxWrapper
from shapely.geometry.base import BaseGeometry

import ra2ce.graph.networks_utils as nut
from ra2ce.graph.osm_network_wrapper.extremities_data import ExtremitiesData


class OsmNetworkWrapper:
    network_dict: dict
    output_path: Path
    graph_crs: str

    def __init__(self, config: dict, graph_crs: str) -> None:
        if not config:
            raise ValueError("Config cannot be None")
        if not config.get("network", {}):
            raise ValueError(
                "A network dictionary is required for creating a OsmNetworkWrapper object."
            )
        if not isinstance(config.get("network"), dict):
            raise ValueError('Config["network"] should be a dictionary')
        self.network_dict = config["network"]
        self.output_path = config["static"] / "output_graph"
        self.graph_crs = graph_crs
        if not self.graph_crs:
            self.graph_crs = "epsg:4326"

    def get_clean_graph_from_osm(self) -> MultiDiGraph:
        """
        Creates a network from a polygon by downloading via the OSM API in its extent.

        Raises:
            FileNotFoundError: When no valid polygon file is provided.

        Returns:
            MultiDiGraph: Complex (clean) graph after download from OSM, for use in the direct analyses and input to
            derive simplified network.
        """
        # It can only read in one geojson
        if not self.network_dict.get("polygon", []):
            raise ValueError("No valid value provided for polygon file.")

        polygon_file = self.output_path.parent.joinpath(
            "network", self.network_dict.get("polygon", [])[0]
        )
        if not polygon_file.is_file():
            raise FileNotFoundError("No polygon_file file found.")

        poly_dict = nut.read_geojson(geojson_file=polygon_file)
        _complex_graph = self._download_clean_graph_from_osm(
            polygon=nut.geojson_to_shp(poly_dict),
            network_type=self.network_dict.get("network_type", ""),
            road_types=self.network_dict.get("road_types", ""),
        )
        return _complex_graph

    def _download_clean_graph_from_osm(
            self, polygon: BaseGeometry, road_types: str, network_type: str
    ) -> MultiDiGraph:
        if not road_types and not network_type:
            raise ValueError("Either of the link_type or network_type should be known")
        elif not road_types:
            # The user specified only the network type.
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type,
                simplify=False,
                retain_all=True,
            )
        elif not network_type:
            # The user specified only the road types.
            cf = f'["highway"~"{road_types.replace(",", "|")}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon, custom_filter=cf, simplify=False, retain_all=True
            )
        else:
            cf = f'["highway"~"{road_types.replace(",", "|")}"]'
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
        if "crs" not in _complex_graph.graph.keys():
            _complex_graph.graph["crs"] = self.graph_crs
        self.get_clean_graph(_complex_graph)
        return _complex_graph

    @staticmethod
    def get_clean_graph(complex_graph: MultiDiGraph):
        complex_graph = OsmNetworkWrapper.drop_duplicates(complex_graph)
        complex_graph = nut.add_missing_geoms_graph(
            graph=complex_graph, geom_name="geometry"
        ).to_directed()
        complex_graph = OsmNetworkWrapper.snap_nodes_to_nodes(
            graph=complex_graph, threshold=0.000025
        )
        return complex_graph

    @staticmethod
    def drop_duplicates(complex_graph: MultiDiGraph) -> MultiDiGraph:
        unique_elements = (
            set()
        )  # This gets updated during the drop_duplicates_in_nodes and drop_duplicates_in_edges

        unique_graph = OsmNetworkWrapper.drop_duplicates_in_nodes(
            unique_elements=unique_elements, graph=complex_graph
        )
        unique_graph = OsmNetworkWrapper.drop_duplicates_in_edges(
            unique_elements=unique_elements,
            unique_graph=unique_graph,
            graph=complex_graph,
        )
        return unique_graph

    @staticmethod
    def drop_duplicates_in_nodes(
            unique_elements: set, graph: MultiDiGraph
    ) -> MultiDiGraph:
        if unique_elements is None or not isinstance(unique_elements, set):
            raise ValueError("unique_elements should be a set")

        unique_graph = nx.MultiDiGraph()
        for node, data in graph.nodes(data=True):
            if data["x"] is None or data["y"] is None:
                raise ValueError(
                    "Incompatible coordinate keys. Check the keys which define the x and y coordinates"
                )

            x, y = data["x"], data["y"]
            coord = (x, y)
            if coord not in unique_elements:
                node_attributes = {key: value for key, value in data.items()}
                unique_graph.add_node(node, **node_attributes)
                unique_elements.add(coord)
        # Copy the graph dictionary from the source one.
        unique_graph.graph = graph.graph
        return unique_graph

    @staticmethod
    def drop_duplicates_in_edges(
            unique_elements: set, unique_graph: MultiDiGraph, graph: MultiDiGraph
    ):
        """
        Checks if both extremities are in the unique_graph (u has not the same coor of v, no line from u to itself is
        allowed). Checks if an edge is already made between such extremities with the given id and coordinates before
        considering it in the unique graph
        """
        if (
                not unique_elements
                or not any(unique_elements)
                or not all(isinstance(item, tuple) for item in unique_elements)
        ):
            raise ValueError(
                """unique_elements cannot be None, empty, or have non-tuple elements. 
            Provide a set with all unique node coordinates as tuples of (x, y)"""
            )
        if unique_graph is None:
            raise ValueError(
                """unique_graph cannot be None. Provide a graph with unique nodes or perform the 
        drop_duplicates_in_nodes on the graph to generate a unique_graph"""
            )

        def validity_check(extremities_tuple) -> bool:
            extremities = extremities_tuple[0]
            return not (
                    extremities.from_to_id is None
                    or extremities.from_to_coor is None
                    or extremities.from_id == extremities.to_id
            )

        def valid_extremity_data(u, v, data) -> tuple[ExtremitiesData, dict]:
            _extremities_data = ExtremitiesData.get_extremities_data_for_sub_graph(
                from_node_id=u,
                to_node_id=v,
                sub_graph=unique_graph,
                graph=graph,
                shared_elements=unique_elements,
            )

            return _extremities_data, data

        for _extremity_data, _edge_data in filter(
                validity_check,
                map(lambda edge: valid_extremity_data(*edge), graph.edges(data=True)),
        ):
            _id_combination = (_extremity_data.from_to_id, _extremity_data.to_from_id)
            _coor_combination = (
                _extremity_data.from_to_coor,
                _extremity_data.to_from_coor,
            )
            if all(
                    _combination not in unique_elements
                    for _combination in [_id_combination, _coor_combination]
            ):
                edge_attributes = {key: value for key, value in _edge_data.items()}
                unique_graph.add_edge(
                    _extremity_data.from_id, _extremity_data.to_id, **edge_attributes
                )
                unique_elements.add(_id_combination)
                unique_elements.add(_coor_combination)

        return unique_graph

    @staticmethod
    def snap_nodes_to_nodes(graph: MultiDiGraph, threshold: float, rebuild_graph=True, dead_ends=False) -> MultiDiGraph:
        return consolidate_intersections(
            G=graph, rebuild_graph=rebuild_graph, tolerance=threshold, dead_ends=dead_ends
        )

    @staticmethod
    def snap_nodes_to_edges(graph: MultiDiGraph, threshold: float):
        osmnx_wrapper = OsmnxWrapper()
        end_points = set([node for node in graph.nodes() if _is_endpoint(graph, node)])

        if not graph.graph or not graph.graph["crs"]:
            graph.graph["crs"] = "epsg:4326"

        nut.add_missing_geoms_graph(graph=graph, geom_name="geometry").to_directed()

        def threshold_check(node_nearest_ed: dict):
            (node, nearest_ed) = next(iter(node_nearest_ed.items()))
            distance = nearest_ed[-1]
            return distance < threshold

        for node_nearest_edge_data in filter(threshold_check,
                                             map(lambda node: osmnx_wrapper.get_node_nearest_edge(
                                                 graph, (graph.nodes[node]['x'], graph.nodes[node]['y'])),
                                                 end_points)):
            (node, nearest_edge) = next(iter(node_nearest_edge_data.items()))
            # nearest_edge
            # projected_node = .interpolate(shply_line.project(row.geometry))
            print(node_nearest_edge_data)

        # ToDo: Make sure the directions make sense after clustering; both for snap_edges.
        raise NotImplementedError("Next thing to do!")


_valid_unique_graph = nx.MultiDiGraph()
_valid_unique_graph.add_node(1, x=1, y=10)
_valid_unique_graph.add_node(2, x=2, y=20)
_valid_unique_graph.add_node(4, x=2, y=40)
_valid_unique_graph.add_node(5, x=3, y=50)

_valid_unique_graph.add_edge(1, 2, x=[1, 2], y=[10, 20])
_valid_unique_graph.add_edge(2, 4, x=[2, 2], y=[20, 40])
_valid_unique_graph.add_edge(1, 4, x=[1, 2], y=[10, 40])
_valid_unique_graph.add_edge(5, 1, x=[3, 1], y=[50, 10])

OsmNetworkWrapper.snap_nodes_to_edges(_valid_unique_graph, threshold=100)
