import logging
from pathlib import Path
from typing import List, Union, Tuple

import networkx as nx
import pandas as pd
import geopandas as gpd
import momepy

from shapely.geometry import Point
from pyproj import CRS
import ra2ce.graph.networks_utils as nut

logger = logging.getLogger()


class VectorNetworkWrapper:
    """
    VectorNetworkWrapper is a class for handling and manipulating vector files.
    It provides methods for reading vector data, cleaning it, and setting up graph and
    network.
    """

    name: str
    region: gpd.GeoDataFrame
    crs: CRS
    input_path: Path
    output_path: Path
    network_dict: dict

    def __init__(self, config: dict) -> None:
        """
        Initializes the VectorNetworkWrapper object.

        Parameters
        ----------
        config : dict
            Configuration dictionary.
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

    def _parse_ini_value(self, value: str):
        """
        Parses a string value from an ini file.

        Parameters
        ----------
        value : str
            Value to parse.

        Returns
        -------
        str or list of str
            If the value contains a comma, it is split and returned as a list,
            otherwise the original value is returned.
        """
        if isinstance(value, str) and "," in value:
            return [v for v in value.split(",")]
        else:
            return value

    def _setup_global(self, config: dict):
        """
        Sets up project properties based on provided configuration.

        Parameters
        ----------
        config : dict
            Project configuration dictionary.
        """
        project_config = config.get("project")
        name = self._parse_ini_value(project_config.get("name", "project_name"))
        region = self._parse_ini_value(project_config.get("region", None))
        crs = self._parse_ini_value(project_config.get("crs", 4326))
        self.name = name
        self.crs = CRS.from_user_input(crs)
        self.region = self.read_vector(region, self.crs)
        self.input_path = config.get("static").joinpath("network")
        self.output_path = config.get("output")

    def _pase_ini_filename(self, filename: str) -> List[Path]:
        """Makes a list of file paths by joining with input path.
        Also checks validity of files.

        Parameters
        ----------
        filename : str
            str of file names seperated by comma (",").

        Returns
        -------
        file_paths : List[Path]
            List of file paths.
        """
        if isinstance(filename, str):
            file_names = filename.split(",")
        else:
            logger.error("file names are not valid.")

        file_paths = [self.input_path.joinpath(f) for f in file_names]
        for f in file_paths:
            if not f.resolve().is_file():
                logger.error(f"vector file {f} is not found.")

        return file_paths

    def _get_network_opt(self, network_config: dict) -> dict:
        """
        Retrieves network options used in this wrapper from provided configuration.

        Parameters
        ----------
        network_config : dict
            Network configuration dictionary.

        Returns
        -------
        dict
            Dictionary of network options.
        """

        files = self._pase_ini_filename(network_config.get("primary_file", None))
        file_id = self._parse_ini_value(
            network_config.get("file_id", None)
        )  # TODO only needed when cleanup based on fid
        file_filter = self._parse_ini_value(network_config.get("filter", None))
        file_crs = self._parse_ini_value(network_config.get("crs", self.crs))  # assumes
        is_directed = self._parse_ini_value(network_config.get("directed", False))
        return dict(
            files=files,
            file_id=file_id,
            file_filter=file_filter,
            file_crs=file_crs,
            is_directed=is_directed,
        )

    def setup_graph_from_vector(
        self, gdf: gpd.GeoDataFrame, is_directed: bool
    ) -> nx.Graph:
        """
        Creates a graph with nodes and edges based on a given GeoDataFrame.

        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            Input geographic data.
        is_directed : bool
            Whether the graph should be directed.

        Returns
        -------
        nx.Graph
            NetworkX graph object.
        """
        digraph = nx.DiGraph(crs=self.crs, name=self.name, approach="primal")
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

        if is_directed:
            return digraph
        return digraph.to_undirected()

    def setup_network_edges_and_nodes_from_graph(
        self,
        graph: nx.Graph,
    ) -> gpd.GeoDataFrame:
        """
        Sets up network nodes and edges from a given graph.

        Parameters
        ----------
        graph : nx.Graph
            Input graph.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the network edges.
            Contain ["edge_fid", "node_A", and "node_B"]
        gpd.GeoDataFrame
            GeoDataFrame representing the network nodes.
            Contain ["node_fid"]
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
            nodes.crs = self.crs
        if not edges.crs:
            edges.crs = self.crs
        return edges, nodes

    def setup_network_from_vector(
        self,
    ) -> Tuple[nx.MultiGraph, gpd.GeoDataFrame]:
        """
        Sets up a network from vector files.

        Returns
        -------
        nx.MultiGraph
            MultiGraph representing the graph.
        gpd.GeoDataFrame
            GeoDataFrame representing the network.
        """
        files = self.network_dict["files"]
        file_crs = self.network_dict["file_crs"]
        is_directed = self.network_dict["is_directed"]

        gdf = self.read_vector(vector_filenames=files, crs=file_crs)
        gdf = self.clean_vector(gdf)
        graph = self.setup_graph_from_vector(gdf, is_directed=is_directed)
        edges, nodes = self.setup_network_edges_and_nodes_from_graph(graph)
        graph_complex = nut.graph_from_gdf(edges, nodes, node_id="node_fid")
        return graph_complex, edges

    def read_vector(
        self, vector_filenames: List[Path], crs: Union[int, str]
    ) -> gpd.GeoDataFrame:
        """
        Reads a vector file or a list of vector files.
        Clips for project region and reproject to project crs if available.

        Parameters
        ----------
        vector_filenames : list[Path]
            List of Path to the vector files.
        crs : Union[int, str]
            Coordinate reference system for the files. Allow only one crs for all  `vector_filenames`.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the vector data.
        """
        gdf = self._read_files(vector_filenames)
        if gdf is None:
            logger.info("no file is read.")
            return None

        # set crs and reproject if needed
        if not gdf.crs and crs:
            gdf = gdf.set_crs(CRS.from_user_input(crs))
            logger.info("setting crs as default EPSG:4326. specify crs if incorrect")

        if self.crs:
            gdf = gdf.to_crs(self.crs)
            logger.info("reproject vector file to project crs")

        # clip for region
        if self.region is not None:
            gdf = gpd.overlay(gdf, self.region, how="intersection", keep_geom_type=True)
            logger.info("clip vector file to project region")

        # validate
        if len(gdf) == 0:
            logger.warning("No vector features found within project region")
            return None

        return gdf

    def _read_files(self, file_list: list[Path]) -> gpd.GeoDataFrame:
        """
        Reads a file or a list of files into a GeoDataFrame.

        Parameters
        ----------
        file_list : list[Path]
            List of file paths.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the data.
        """
        # read file
        if isinstance(file_list, list):
            gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(_fn) for _fn in file_list]))
            logger.info("read vector files.")
        else:
            gdf = None
            logger.info("no file is read.")
        return gdf

    def clean_vector(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Cleans a GeoDataFrame.
        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            Input GeoDataFrame.

        Returns
        -------
        gpd.GeoDataFrame
            Cleaned GeoDataFrame.
        """
        # preprocessing before cleanup
        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(gdf)

        return gdf

    @staticmethod
    def explode_and_deduplicate_geometries(gpd: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Explodes and deduplicates geometries a GeoDataFrame.

        Parameters
        ----------
        gpd : gpd.GeoDataFrame
            Input GeoDataFrame.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame with exploded and deduplicated geometries.
        """
        gpd = gpd.explode()
        gpd = gpd[
            gpd.index.isin(
                gpd["geometry"].apply(lambda geom: geom.wkb).drop_duplicates().index
            )
        ]
        return gpd
