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

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx
import pyproj
from geopandas import GeoDataFrame
from networkx import MultiDiGraph, MultiGraph
from shapely.geometry.base import BaseGeometry

import ra2ce.network.networks_utils as nut
from ra2ce.network.avg_speed.avg_speed_calculator import AvgSpeedCalculator
from ra2ce.network.exporters.json_exporter import JsonExporter
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_simplification import NetworkGraphSimplificator
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.extremities_data import (
    ExtremitiesData,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_utils import (
    get_node_nearest_edge,
    is_endnode_check,
    modify_graph,
)
from ra2ce.network.segmentation import Segmentation


class OsmNetworkWrapper(NetworkWrapperProtocol):

    polygon_graph: MultiDiGraph
    network_type: NetworkTypeEnum
    road_types: list[RoadTypeEnum]

    def __init__(self, config_data: NetworkConfigData) -> None:
        self.attributes_to_exclude_in_simplification = (
            config_data.network.attributes_to_exclude_in_simplification
        )
        self.output_graph_dir = config_data.output_graph_dir
        self.crs = config_data.crs

        # Network
        self.network_type = config_data.network.network_type
        self.road_types = config_data.network.road_types
        self.polygon_graph = self._get_clean_graph_from_osm(config_data.network.polygon)
        self.is_directed = config_data.network.directed
        self.link_type_column = config_data.network.link_type_column

        # Cleanup
        self.segmentation_length = config_data.cleanup.segmentation_length

    @classmethod
    def with_polygon(
        cls, config_data: NetworkConfigData, polygon: BaseGeometry
    ) -> OsmNetworkWrapper:
        """
        Gets an `OsmNetworkWrapper` with the given `polygon` transformed into a
        clean graph as the `polygon_graph` property.

        Args:
            polygon (BaseGeometry): Base polygon from which to generate the graph.

        Returns:
            OsmNetworkWrapper: Wrapper with valid `polygon_graph` property.
        """
        _wrapper = cls(config_data)
        _clean_graph = _wrapper._download_clean_graph_from_osm(
            polygon=polygon,
            network_type=_wrapper.network_type,
            road_types=_wrapper.road_types,
        )
        _wrapper.polygon_graph = _clean_graph
        return _wrapper

    @staticmethod
    def get_network_from_polygon(
        config_data: NetworkConfigData, polygon: BaseGeometry
    ) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets a valid network (`MultiGraph` and `GeoDataFrame`) for the given network configuration and
        boundary box (represented by a `shapely.BaseGeometry`).

        Args:
            config_data (NetworkConfigData): Network data configuration required for OSM download.
            polygon (BaseGeometry): Polygon representing the boundary box.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Resulting network representations.
        """
        _network_wrapper = OsmNetworkWrapper.with_polygon(config_data, polygon)
        return _network_wrapper.get_network()

    @staticmethod
    def get_network_from_geojson(config_data: NetworkConfigData):
        """
        Gets a valid network (`MultiGraph` and `GeoDataFrame`) for the given network configuration,
        given that its network section contains a valid path for the polygon property.

        Args:
            config_data (NetworkConfigData): Network data configuration required for OSM download.

        Raises:
            ValueError: When the `NetworkConfigData` does not contain a valid polygon path
            for its network section.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Resulting network representations.
        """
        if (
            not isinstance(config_data.network.polygon, Path)
            or not config_data.network.polygon.is_file()
        ):
            raise ValueError(
                "A valid network polygon (.geojson) file path needs to be provided."
            )

        return OsmNetworkWrapper(config_data).get_network()

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:

        # Create 'graph_simple'
        graph_simple, graph_complex, link_tables = NetworkGraphSimplificator(
            graph_complex=self.polygon_graph,
            attributes_to_exclude=self.attributes_to_exclude_in_simplification,
        ).simplify()

        # Assign the average speed and time to the graphs
        graph_simple = AvgSpeedCalculator(
            graph_simple, self.link_type_column, self.output_graph_dir
        ).assign()
        graph_complex = AvgSpeedCalculator(
            graph_complex, self.link_type_column, self.output_graph_dir
        ).assign()

        # Create 'edges_complex', convert complex graph to geodataframe
        logging.info("Start converting the graph to a geodataframe")
        edges_complex, _ = nut.graph_to_gdf(graph_complex)
        logging.info("Finished converting the graph to a geodataframe")

        # Segment the complex graph
        edges_complex, link_tables = Segmentation.segment_graph(
            self.segmentation_length,
            self.crs,
            edges_complex,
            export_link_table=True,
            link_tables=link_tables,
        )

        # Save the link tables linking complex and simple IDs
        self._export_linking_tables(link_tables)

        if not self.is_directed and isinstance(graph_simple, MultiDiGraph):
            graph_simple = graph_simple.to_undirected()

        # Check if all geometries between nodes are there, if not, add them as a straight line.
        graph_simple = nut.add_missing_geoms_graph(graph_simple, geom_name="geometry")

        return graph_simple, edges_complex

    def _export_linking_tables(self, linking_tables: tuple[Any]) -> None:
        if not self.output_graph_dir:
            logging.warning(
                "No `output_graph_dir` is set, therefore no intermediate results will be exported."
            )
            return
        _exporter = JsonExporter()
        _exporter.export(
            self.output_graph_dir.joinpath("simple_to_complex.json"), linking_tables[0]
        )
        _exporter.export(
            self.output_graph_dir.joinpath("complex_to_simple.json"), linking_tables[1]
        )

    def _get_clean_graph_from_osm(self, polygon_path: Path) -> MultiDiGraph | None:
        """
        Creates a network from a polygon by downloading via the OSM API in its extent.

        Args:
            polygon_path (Path): Path where the polygon file can be found.

        Returns:
            MultiDiGraph: Complex (clean) graph after download from OSM, for use in the damages analyses and input to derive simplified network.
        """
        # It can only read in one geojson
        if not isinstance(polygon_path, Path):
            logging.warning("No valid value provided for polygon file.")
            return None
        elif not polygon_path.is_file():
            logging.error("No polygon_file file found at {}.".format(polygon_path))
            return None

        _normalized_polygon = nut.get_normalized_geojson_polygon(polygon_path)
        _complex_graph = self._download_clean_graph_from_osm(
            polygon=_normalized_polygon,
            network_type=self.network_type,
            road_types=self.road_types,
        )
        return _complex_graph

    def _download_clean_graph_from_osm(
        self,
        polygon: BaseGeometry,
        road_types: list[RoadTypeEnum],
        network_type: NetworkTypeEnum,
    ) -> MultiDiGraph:
        _available_road_types = road_types and any(road_types)
        _road_types_as_str = (
            list(map(lambda x: x.config_value, road_types))
            if _available_road_types
            else []
        )

        if not _available_road_types and not network_type:
            raise ValueError("Either of the link_type or network_type should be known")
        elif not _available_road_types:
            # The user specified only the network type.
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type.config_value,
                simplify=False,
                retain_all=True,
            )
        elif not network_type:
            # The user specified only the road types.
            cf = f'["highway"~"{"|".join(_road_types_as_str)}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon, custom_filter=cf, simplify=False, retain_all=True
            )
        else:
            # _available_road_types and network_type
            cf = f'["highway"~"{"|".join(_road_types_as_str)}"]'
            _complex_graph = osmnx.graph_from_polygon(
                polygon=polygon,
                network_type=network_type.config_value,
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
            _complex_graph.graph["crs"] = self.crs
        self.get_clean_graph(_complex_graph)
        return _complex_graph

    @staticmethod
    def get_clean_graph(complex_graph: MultiDiGraph):
        complex_graph = OsmNetworkWrapper.drop_duplicates(complex_graph)
        complex_graph = nut.add_missing_geoms_graph(
            graph=complex_graph, geom_name="geometry"
        ).to_directed()
        complex_graph = OsmNetworkWrapper.snap_nodes_to_nodes(
            graph=complex_graph, threshold=0.00005
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
    def snap_nodes_to_edges(graph: MultiDiGraph, threshold: float) -> MultiDiGraph:
        def threshold_check(node_nearest_ed: dict):
            distance = node_nearest_ed["nearest_edge"][-1]
            return distance <= threshold

        end_nodes = [
            node for node in graph.nodes(data=True) if is_endnode_check(graph, node[0])
        ]

        if (
            not graph.graph
            or not graph.graph["crs"]
            or isinstance(graph.graph["crs"], str)
        ):
            graph.graph["crs"] = pyproj.CRS("epsg:4326")
        nut.add_missing_geoms_graph(graph=graph, geom_name="geometry").to_directed()

        for node_nearest_edge_data in filter(
            threshold_check,
            map(lambda end_node: get_node_nearest_edge(graph, end_node), end_nodes),
        ):
            modify_graph(graph=graph, node_nearest_edge_data=node_nearest_edge_data)
        return graph
