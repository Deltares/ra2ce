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
            self.graph_crs = "EPSG:4326"

    def download_graph_from_osm(self) -> MultiDiGraph:
        if not self.network_dict.get("polygon", None):
            raise FileNotFoundError(
                "No or invalid polygon file is introduced for OSM download"
            )
        polygon_file = self.output_path.parent.joinpath(
            "network", self.network_dict["polygon"]
        )
        if not polygon_file.exists():
            raise FileNotFoundError("No polygon_file file found")
        poly_dict = nut.read_geojson(
            geojson_file=polygon_file
        )  # It can only read in one geojson

        _complex_graph = self.get_graph_from_osm_download(
            polygon=nut.geojson_to_shp(poly_dict),
            network_type=self.network_dict.get("network_type", ""),
            link_type=self.network_dict.get("road_type", ""),
        )
        _complex_graph.graph["crs"] = self.graph_crs
        self.get_clean_graph(_complex_graph)
        return _complex_graph

    def get_graph_from_osm_download(
        self, polygon: BaseGeometry, link_type: str, network_type: str
    ) -> MultiDiGraph:
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
        if not link_type and not network_type:
            raise ValueError("Either of the link_type or network_type should be known")
        elif not link_type:
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
                polygon=polygon, custom_filter=cf, simplify=False, retain_all=True
            )
        elif link_type and network_type:
            cf = f'["highway"~"{link_type.replace(",", "|")}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type,
                custom_filter=cf,
                simplify=False,
                retain_all=True,
            )
        else:
            # The user specified the network type and road types.
            raise ValueError("This case is not supported")
        logging.info(
            "graph downloaded from OSM with {:,} nodes and {:,} edges".format(
                len(list(_complex_graph.nodes())), len(list(_complex_graph.edges()))
            )
        )
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
    def drop_duplicates_in_nodes(unique_elements: set, graph: MultiDiGraph):
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
    def snap_nodes_to_nodes(graph, threshold):
        return consolidate_intersections(
            G=graph, rebuild_graph=True, tolerance=threshold, dead_ends=False
        )

    @staticmethod
    def snap_nodes_to_edges(graph, threshold):
        raise NotImplementedError("Next thing to do!")
