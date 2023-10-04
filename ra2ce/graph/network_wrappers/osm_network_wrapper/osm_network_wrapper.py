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
from typing import Any

import networkx as nx
import osmnx
import pandas as pd
from geopandas import GeoDataFrame
from networkx import MultiDiGraph, MultiGraph
from shapely.geometry.base import BaseGeometry

import ra2ce.graph.networks_utils as nut
from ra2ce.graph.exporters.json_exporter import JsonExporter
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_wrappers.network_wrapper_protocol import NetworkWrapperProtocol
from ra2ce.graph.network_wrappers.osm_network_wrapper.extremities_data import (
    ExtremitiesData,
)


class OsmNetworkWrapper(NetworkWrapperProtocol):
    def __init__(self, config_data: NetworkConfigData) -> None:
        self.output_graph_dir = config_data.output_graph_dir
        self.graph_crs = config_data.crs

        # Network options
        self.network_type = config_data.network.network_type
        self.road_types = config_data.network.road_types
        self.polygon_path = config_data.network.polygon
        self.is_directed = config_data.network.directed

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets an indirected graph

        Returns:
            tuple[MultiGraph, GeoDataFrame]: _description_
        """
        logging.info("Start downloading a network from OSM.")
        graph_complex = self.get_clean_graph_from_osm()

        # Create 'graph_simple'
        graph_simple, graph_complex, link_tables = nut.create_simplified_graph(
            graph_complex
        )

        # Create 'edges_complex', convert complex graph to geodataframe
        logging.info("Start converting the graph to a geodataframe")
        edges_complex, node_complex = nut.graph_to_gdf(graph_complex)
        logging.info("Finished converting the graph to a geodataframe")

        # Save the link tables linking complex and simple IDs
        self._export_linking_tables(link_tables)

        if not self.is_directed and isinstance(graph_simple, MultiDiGraph):
            graph_simple = graph_simple.to_undirected()

        # Check if all geometries between nodes are there, if not, add them as a straight line.
        graph_simple = nut.add_missing_geoms_graph(graph_simple, geom_name="geometry")
        graph_simple = self._get_avg_speed(graph_simple)
        return graph_simple, edges_complex

    def _get_avg_speed(
        self, original_graph: nx.classes.graph.Graph
    ) -> nx.classes.graph.Graph:
        if all(["length" in e for u, v, e in original_graph.edges.data()]) and any(
            ["maxspeed" in e for u, v, e in original_graph.edges.data()]
        ):
            # Add time weighing - Define and assign average speeds; or take the average speed from an existing CSV
            path_avg_speed = self.output_graph_dir.joinpath("avg_speed.csv")
            if path_avg_speed.is_file():
                avg_speeds = pd.read_csv(path_avg_speed)
            else:
                avg_speeds = nut.calc_avg_speed(
                    original_graph,
                    "highway",
                    save_csv=True,
                    save_path=path_avg_speed,
                )
            original_graph = nut.assign_avg_speed(original_graph, avg_speeds, "highway")

            # make a time value of seconds, length of road streches is in meters
            for u, v, k, edata in original_graph.edges.data(keys=True):
                hours = (edata["length"] / 1000) / edata["avgspeed"]
                original_graph[u][v][k]["time"] = round(hours * 3600, 0)

            return original_graph
        logging.info(
            "No attributes found in the graph to estimate average speed per network segment."
        )
        return original_graph

    def _export_linking_tables(self, linking_tables: tuple[Any]) -> None:
        _exporter = JsonExporter()
        _exporter.export(
            self.output_graph_dir.joinpath("simple_to_complex.json"), linking_tables[0]
        )
        _exporter.export(
            self.output_graph_dir.joinpath("complex_to_simple.json"), linking_tables[1]
        )

    def get_clean_graph_from_osm(self) -> MultiDiGraph:
        """
        Creates a network from a polygon by by downloading via the OSM API in its extent.

        Raises:
            FileNotFoundError: When no valid polygon file is provided.

        Returns:
            MultiDiGraph: Complex (clean) graph after download from OSM, for use in the direct analyses and input to derive simplified network.
        """
        # It can only read in one geojson
        if not isinstance(self.polygon_path, Path):
            raise ValueError("No valid value provided for polygon file.")
        if not self.polygon_path.is_file():
            raise FileNotFoundError(
                "No polygon_file file found at {}.".format(self.polygon_path)
            )

        poly_dict = nut.read_geojson(geojson_file=self.polygon_path)
        _complex_graph = self._download_clean_graph_from_osm(
            polygon=nut.geojson_to_shp(poly_dict),
            network_type=self.network_type,
            road_types=self.road_types,
        )
        return _complex_graph

    def _download_clean_graph_from_osm(
        self, polygon: BaseGeometry, road_types: list[str], network_type: str
    ) -> MultiDiGraph:
        _available_road_types = road_types and any(road_types)
        if not _available_road_types and not network_type:
            raise ValueError("Either of the link_type or network_type should be known")
        elif not _available_road_types:
            # The user specified only the network type.
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type,
                simplify=False,
                retain_all=True,
            )
        elif not network_type:
            # The user specified only the road types.
            cf = f'["highway"~"{"|".join(road_types)}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon, custom_filter=cf, simplify=False, retain_all=True
            )
        else:
            # _available_road_types and network_type
            cf = f'["highway"~"{"|".join(road_types)}"]'
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
        _complex_graph = self.get_clean_graph(_complex_graph)
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
    def snap_nodes_to_nodes(graph: MultiDiGraph, threshold: float) -> MultiDiGraph:
        return osmnx.consolidate_intersections(
            G=graph, rebuild_graph=True, tolerance=threshold, dead_ends=False
        )

    @staticmethod
    def snap_nodes_to_edges(graph: MultiDiGraph, threshold: float):
        raise NotImplementedError("Next thing to do!")
