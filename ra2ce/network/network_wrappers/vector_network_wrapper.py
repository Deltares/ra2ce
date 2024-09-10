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

import geopandas as gpd
import momepy
import networkx as nx
import pandas as pd
import pyproj
from shapely.geometry import Point
from tqdm import tqdm

import ra2ce.network.networks_utils as nut
from ra2ce.network.avg_speed.avg_speed_calculator import AvgSpeedCalculator
from ra2ce.network.exporters.json_exporter import JsonExporter
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_simplification import NetworkGraphSimplificator
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.segmentation import Segmentation


class VectorNetworkWrapper(NetworkWrapperProtocol):
    """A class for handling and manipulating vector files.

    Provides methods for reading vector data, cleaning it, and setting up graph and
    network.
    """

    def __init__(
        self,
        config_data: NetworkConfigData,
    ) -> None:
        self.attributes_to_exclude_in_simplification = (
            config_data.network.attributes_to_exclude_in_simplification
        )
        self.crs = config_data.crs

        # Network options
        self.primary_files = config_data.network.primary_file
        self.directed = config_data.network.directed

        # Origins Destinations
        self.region_path = config_data.origins_destinations.region
        self.file_id = config_data.network.file_id
        self.link_type_column = config_data.network.link_type_column
        self.output_graph_dir = config_data.output_graph_dir

        # Cleanup
        self.segmentation_length = config_data.cleanup.segmentation_length
        self.delete_duplicate_nodes = config_data.cleanup.delete_duplicate_nodes

    def get_network(
        self,
    ) -> tuple[nx.Graph, gpd.GeoDataFrame]:
        """Gets a network built from vector files.

        Returns:
            nx.MultiGraph: MultiGraph representing the graph.
            gpd.GeoDataFrame: GeoDataFrame representing the network.
        """
        gdf = self._read_vector_to_project_region_and_crs()
        gdf = self.clean_vector(gdf)
        if self.directed:
            graph = self._get_direct_graph_from_vector(
                gdf=gdf,
                edge_attributes_to_include=[
                    "lanes",
                    "length",
                    "maxspeed",
                    "avgspeed",
                    "bridge",
                    "tunnel",
                ],
            )
        else:
            graph = self._get_undirected_graph_from_vector(
                gdf,
                edge_attributes_to_include=[
                    "lanes",
                    "length",
                    "maxspeed",
                    "avgspeed",
                    "bridge",
                    "tunnel",
                ],
            )
        edges, nodes = self.get_network_edges_and_nodes_from_graph(graph)
        graph_complex = nut.graph_from_gdf(edges, nodes, node_id="node_fid")
        if self.delete_duplicate_nodes:
            graph_complex = self._delete_duplicate_nodes(graph_complex)

        logging.info("Start converting the complex graph to a simple graph")
        # Create 'graph_simple'
        graph_simple, graph_complex, link_tables = NetworkGraphSimplificator(
            graph_complex=graph_complex,
            attributes_to_exclude=self.attributes_to_exclude_in_simplification,
        ).simplify()

        # Assign the average speed and time to the graphs
        graph_simple = AvgSpeedCalculator(
            graph_simple, self.link_type_column, self.output_graph_dir
        ).assign()
        graph_complex = AvgSpeedCalculator(
            graph_complex, self.link_type_column, self.output_graph_dir
        ).assign()

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

        if not self.directed and isinstance(graph_simple, nx.MultiDiGraph):
            graph_simple = graph_simple.to_undirected()

        # Check if all geometries between nodes are there, if not, add them as a straight line.
        graph_simple = nut.add_missing_geoms_graph(graph_simple, geom_name="geometry")

        #  Update rfid_c after segmentation, which created more edges n teh complex graph
        graph_simple = nut.add_complex_id_to_graph_simple(
            graph_simple, link_tables[0], "rfid"
        )

        logging.info("Finished converting the complex graph to a simple graph")

        return graph_simple, edges_complex

    def _read_vector_to_project_region_and_crs(self) -> gpd.GeoDataFrame:
        gdf = self._read_files(self.primary_files)
        if gdf is None:
            logging.info("no file is read.")
            return None

        # set crs and reproject if needed
        if not gdf.crs and self.crs:
            gdf = gdf.set_crs(self.crs)
            logging.info("setting crs as default EPSG:4326. specify crs if incorrect")

        if self.crs:
            gdf = gdf.to_crs(self.crs)
            logging.info("reproject vector file to project crs")

        # clip for region
        if self.region_path:
            _region_gpd = self._read_files([self.region_path])
            gdf = gpd.overlay(gdf, _region_gpd, how="intersection", keep_geom_type=True)
            logging.info("clip vector file to project region")

        # validate
        if not any(gdf):
            logging.warning("No vector features found within project region")
            return None

        return gdf

    def _read_files(self, file_list: list[Path]) -> gpd.GeoDataFrame:
        """Reads a list of files into a GeoDataFrame.

        Args:
            file_list (list[Path]): List of file paths.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame representing the data.
        """
        # read file
        gdf = gpd.GeoDataFrame(
            pd.concat([gpd.read_file(_fl, engine="pyogrio") for _fl in file_list])
        )
        logging.info(
            "Read files {} into a 'GeoDataFrame'.".format(
                ", ".join(map(str, file_list))
            )
        )
        return gdf

    @staticmethod
    def _delete_duplicate_nodes(graph_complex: nx.MultiGraph) -> nx.MultiGraph:
        # Create a mapping from location to a representative node
        location_to_representative = {}

        # Iterate through nodes and add representative nodes to the mapping
        for node, data in tqdm(
            graph_complex.nodes(data=True),
            desc="Creating graph with removed node duplicates",
        ):
            location = (round(data["geometry"].x, 7), round(data["geometry"].y, 7))
            if location not in location_to_representative:
                location_to_representative[location] = node

        # Create an updated graph with representative nodes
        updated_graph = nx.MultiGraph()

        updated_graph.add_nodes_from(
            (representative_node, {"geometry": Point(location)})
            for location, representative_node in location_to_representative.items()
        )

        # Add edges to the updated_graph
        for u, v, data in tqdm(
            graph_complex.edges(data=True), desc="Adding edges to the updated graph"
        ):
            u_representative = location_to_representative.get(
                (
                    round(graph_complex.nodes[u]["geometry"].x, 7),
                    round(graph_complex.nodes[u]["geometry"].y, 7),
                )
            )
            v_representative = location_to_representative.get(
                (
                    round(graph_complex.nodes[v]["geometry"].x, 7),
                    round(graph_complex.nodes[v]["geometry"].y, 7),
                )
            )

            if u_representative is not None and v_representative is not None:
                # Add representative nodes if they don't exist in the updated graph
                if not updated_graph.has_node(u_representative):
                    updated_graph.add_node(
                        u_representative,
                        geometry=Point(
                            (
                                round(graph_complex.nodes[u]["geometry"].x, 7),
                                round(graph_complex.nodes[u]["geometry"].y, 7),
                            )
                        ),
                    )

                if not updated_graph.has_node(v_representative):
                    updated_graph.add_node(
                        v_representative,
                        geometry=Point(
                            (
                                round(graph_complex.nodes[v]["geometry"].x, 7),
                                round(graph_complex.nodes[v]["geometry"].y, 7),
                            )
                        ),
                    )

                # Add edges to the updated graph
                updated_graph.add_edge(u_representative, v_representative, **data)

        # Set the CRS for updated_graph equal to the CRS of graph_complex
        updated_graph.graph["crs"] = graph_complex.graph.get(
            "crs", pyproj.CRS("EPSG:4326")
        )
        updated_graph.graph["name"] = graph_complex.graph.get("name", None)
        return updated_graph

    def _create_graph_from_gdf(
        self,
        geo_dataframe: gpd.GeoDataFrame,
        edge_attributes_to_include: list,
    ) -> nx.Graph | nx.DiGraph:
        """
        Creates a simple undirected graph with node and edge geometries based on a given GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame containing line geometries.
                Allow both LineString and MultiLineString.
            edge_attributes_to_include (List[str], optional): Additional attributes to include from the GeoDataFrame in the graph.

        Returns:
            nx.Graph: NetworkX graph object with node and edge geometries and specified attributes.
        """
        _networkx_graph = nx.DiGraph(crs=geo_dataframe.crs, approach="primal")

        for _, row in geo_dataframe.iterrows():
            link_id = row.get(self.file_id, None)
            link_type = row.get(self.link_type_column, None)

            from_node = row.geometry.coords[0]
            to_node = row.geometry.coords[-1]
            _edge_attributes = {
                f"{self.file_id}": link_id,
                f"{self.link_type_column}": link_type,
                "avgspeed": row.pop("avgspeed") if "avgspeed" in row else None,
                "geometry": row.pop("geometry"),
            }
            _networkx_graph.add_node(from_node, geometry=Point(from_node))
            _networkx_graph.add_node(to_node, geometry=Point(to_node))
            _networkx_graph.add_edge(
                from_node,
                to_node,
                link_id=link_id,
                **_edge_attributes,
            )
            if edge_attributes_to_include:
                for edge_attribute_to_include in edge_attributes_to_include:
                    edge_attribute = (
                        row[edge_attribute_to_include]
                        if edge_attribute_to_include in row
                        else None
                    )
                    if edge_attribute:
                        edge_data = _networkx_graph[from_node][to_node]
                        edge_data[edge_attribute_to_include] = edge_attribute

        return _networkx_graph

    def _get_direct_graph_from_vector(
        self, gdf: gpd.GeoDataFrame, edge_attributes_to_include: list
    ) -> nx.DiGraph:
        """Creates a simple directed graph with node and edge geometries based on a given GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame containing line geometries.
                Allow both LineString and MultiLineString.
            edge_attributes_to_include: Attributes needed to be included from gdf in the graph


        Returns:
            nx.DiGraph: NetworkX graph object with "crs", "approach" as graph properties.
        """

        # simple geometry handling
        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(gdf)

        # to graph
        return self._create_graph_from_gdf(gdf, edge_attributes_to_include)

    def _get_undirected_graph_from_vector(
        self, gdf: gpd.GeoDataFrame, edge_attributes_to_include: list
    ) -> nx.Graph:
        """Creates a simple undirected graph with node and edge geometries based on a given GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame containing line geometries.
                Allow both LineString and MultiLineString.
            edge_attributes_to_include: Attributes needed to be included from gdf in the graph

        Returns:
            nx.Graph: NetworkX graph object with "crs", "approach" as graph properties.
        """
        digraph = self._get_direct_graph_from_vector(
            gdf=gdf, edge_attributes_to_include=edge_attributes_to_include
        )
        return digraph.to_undirected()

    @staticmethod
    def get_network_edges_and_nodes_from_graph(
        graph: nx.Graph,
    ) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Sets up network nodes and edges from a given graph.

        Args:
            graph (nx.Graph): Input graph with geometry for nodes and edges.
                Must contain "crs" as graph property.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame representing the network edges with "edge_fid", "node_A", and "node_B".
            gpd.GeoDataFrame: GeoDataFrame representing the network nodes with "node_fid".
        """

        # TODO ths function use conventions. Good to make consistant convention with osm
        nodes, edges = momepy.nx_to_gdf(graph, nodeID="node_fid")
        edges["edge_fid"] = (
            edges["node_start"].astype(str) + "_" + edges["node_end"].astype(str)
        )
        edges.rename(
            {"node_start": "node_A", "node_end": "node_B"}, axis=1, inplace=True
        )
        if not nodes.crs:
            nodes.crs = graph.graph["crs"]
        if not edges.crs:
            edges.crs = graph.graph["crs"]

        if "fid" in edges.columns:
            edges = edges.drop(columns=["fid"])
        return edges, nodes

    @staticmethod
    def clean_vector(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Cleans a GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame.

        Returns:
            gpd.GeoDataFrame: Cleaned GeoDataFrame.
        """

        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(gdf)

        return gdf

    @staticmethod
    def explode_and_deduplicate_geometries(gpd: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Explodes and deduplicates geometries a GeoDataFrame.

        Args:
            gpd (gpd.GeoDataFrame): Input GeoDataFrame.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with exploded and deduplicated geometries.
        """
        gpd = gpd.explode()
        gpd = gpd[
            gpd.index.isin(
                gpd.geometry.apply(lambda geom: geom.wkb).drop_duplicates().index
            )
        ]
        return gpd

    def _export_linking_tables(self, linking_tables: tuple[Any]) -> None:
        _exporter = JsonExporter()
        _exporter.export(
            self.output_graph_dir.joinpath("simple_to_complex.json"), linking_tables[0]
        )
        _exporter.export(
            self.output_graph_dir.joinpath("complex_to_simple.json"), linking_tables[1]
        )
