import logging
from pathlib import Path
from typing import Union

import networkx as nx
import pandas as pd
import geopandas as gpd
import momepy

from shapely.geometry import Point
from pyproj import CRS
import ra2ce.graph.networks_utils as nut

logger = logging.getLogger()


class VectorNetworkWrapper:
    """A class for handling and manipulating vector files.

    Provides methods for reading vector data, cleaning it, and setting up graph and
    network.
    """

    name: str
    region: gpd.GeoDataFrame
    crs: CRS
    input_path: Path
    output_path: Path
    network_dict: dict

    def __init__(self, config: dict) -> None:
        """Initializes the VectorNetworkWrapper object.

        Args:
            config (dict): Configuration dictionary.

        Raises:
            ValueError: If the config is None or doesn't contain a network dictionary,
                or if config['network'] is not a dictionary.
        """

        if not config:
            raise ValueError("Config cannot be None")
        if not config.get("network", {}):
            raise ValueError(
                "A network dictionary is required for creating a "
                + f"{self.__class__.__name__} object."
            )
        if not isinstance(config.get("network"), dict):
            raise ValueError('Config["network"] should be a dictionary')

        self._setup_global(config)
        self.network_dict = self._get_network_opt(config["network"])

    def _parse_ini_stringlist(self, value: str) -> Union[str, list, None]:
        """Parses a string with "," into a list from an ini file.

        Args:
            value (str): Value to parse.

        Returns:
            list of str If the value contains a comma, it is split and returned
                as a list, otherwise the original value is returned.
                None if the value is an empty string.
        """
        if not value:
            return None
        elif isinstance(value, str) and "," in value:
            return value.split(",")
        else:
            return value

    def _setup_global(self, config: dict) -> None:
        """Sets up project properties based on provided configuration.

        Args:
            config (dict): Project configuration dictionary.
        """
        self.input_path = config.get("static").joinpath("network")
        self.output_path = config.get("output")

        project_config = config.get("project")
        name = project_config.get("name", "project_name")
        region = project_config.get("region", None)
        crs = project_config.get("crs", 4326)
        self.name = name
        self.crs = CRS.from_user_input(crs)
        self.region = self._read_files([Path(region)]) if region else region

    def _parse_ini_filenamelist(self, filename: str) -> list[Path]:
        """Makes a list of file paths by joining with input path and checks validity of files.

        Args:
            filename (str): String of file names separated by comma (",").

        Returns:
            List[Path]: List of file paths.
        """
        if not isinstance(filename, str):
            logger.error("file names are not valid.")

        file_paths = [self.input_path.joinpath(f.strip()) for f in filename.split(",")]

        for f in file_paths:
            if not f.resolve().is_file():
                logger.error(f"vector file {f} is not found.")

        return file_paths

    def _get_network_opt(self, network_config: dict) -> dict:
        """Retrieves network options used in this wrapper from provided configuration.

        Args:
            network_config (dict): Network configuration dictionary.

        Returns:
            dict: Dictionary of network options.
        """

        files = self._parse_ini_filenamelist(network_config.get("primary_file", ""))
        file_id = self._parse_ini_stringlist(
            network_config.get("file_id", "")
        )  # only needed when cleanup based on fid
        file_filter = self._parse_ini_stringlist(network_config.get("filter", ""))
        file_crs = CRS.from_user_input(network_config.get("crs", self.crs))
        is_directed = network_config.get("directed", False)
        return dict(
            files=files,
            file_id=file_id,
            file_filter=file_filter,
            file_crs=file_crs,
            is_directed=is_directed,
        )

    @staticmethod
    def setup_digraph_from_vector(gdf: gpd.GeoDataFrame) -> nx.DiGraph:
        """Creates a simple directed graph with node and edge geometries based on a given GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame containing line geometries.
                Allow both LineString and MultiLineString.

        Returns:
            nx.DiGraph: NetworkX graph object with "crs", "approach" as graph properties.
        """

        # simple geometry handeling
        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(gdf)

        # to graph
        digraph = nx.DiGraph(crs=gdf.crs, approach="primal")
        for index, row in gdf.iterrows():
            from_node = row.geometry.coords[0]
            to_node = row.geometry.coords[-1]
            digraph.add_node(from_node, geometry=Point(from_node))
            digraph.add_node(to_node, geometry=Point(to_node))
            digraph.add_edge(
                from_node,
                to_node,
                geometry=row.pop(
                    "geometry"
                ),  # **row TODO: check if we do need all columns
            )

        return digraph

    @staticmethod
    def setup_graph_from_vector(gdf: gpd.GeoDataFrame) -> nx.Graph:
        """Creates a simple undirected graph with node and edge geometries based on a given GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame containing line geometries.
                Allow both LineString and MultiLineString.

        Returns:
            nx.Graph: NetworkX graph object with "crs", "approach" as graph properties.
        """
        digraph = VectorNetworkWrapper.setup_digraph_from_vector(gdf)
        return digraph.to_undirected()

    @staticmethod
    def setup_network_edges_and_nodes_from_graph(
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
        return edges, nodes

    def setup_network_from_vector(
        self,
    ) -> tuple[nx.MultiGraph, gpd.GeoDataFrame]:
        """Sets up a network from vector files.

        Returns:
            nx.MultiGraph: MultiGraph representing the graph.
            gpd.GeoDataFrame: GeoDataFrame representing the network.
        """
        files = self.network_dict["files"]
        file_crs = self.network_dict["file_crs"]
        is_directed = self.network_dict["is_directed"]

        gdf = self._read_vector_to_project_region_and_crs(
            vector_filenames=files, crs=file_crs
        )
        gdf = VectorNetworkWrapper.clean_vector(gdf)
        if is_directed:
            graph = VectorNetworkWrapper.setup_digraph_from_vector(gdf)
        else:
            graph = VectorNetworkWrapper.setup_graph_from_vector(gdf)
        edges, nodes = VectorNetworkWrapper.setup_network_edges_and_nodes_from_graph(
            graph
        )
        graph_complex = nut.graph_from_gdf(edges, nodes, node_id="node_fid")
        return graph_complex, edges

    def _read_vector_to_project_region_and_crs(
        self, vector_filenames: list[Path], crs: CRS
    ) -> gpd.GeoDataFrame:
        """Reads a vector file or a list of vector files.

        Clips for project region and reproject to project crs if available.
        Explodes multi geometry into single geometry.

        Args:
            vector_filenames (list[Path]): List of Path to the vector files.
            crs (CRS): Coordinate reference system for the files. Allow only one crs for all  `vector_filenames`.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame representing the vector data.
        """
        gdf = self._read_files(vector_filenames)
        if gdf is None:
            logger.info("no file is read.")
            return None

        # set crs and reproject if needed
        if not gdf.crs and crs:
            gdf = gdf.set_crs(crs)
            logger.info("setting crs as default EPSG:4326. specify crs if incorrect")

        if self.crs:
            gdf = gdf.to_crs(self.crs)
            logger.info("reproject vector file to project crs")

        # clip for region
        if self.region is not None:
            gdf = gpd.overlay(gdf, self.region, how="intersection", keep_geom_type=True)
            logger.info("clip vector file to project region")

        # validate
        if not any(gdf):
            logger.warning("No vector features found within project region")
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
        if isinstance(file_list, list):
            gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(_fn) for _fn in file_list]))
            logger.info("read vector files.")
        else:
            gdf = None
            logger.info("no file is read.")
        return gdf

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
