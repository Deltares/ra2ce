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
from ra2ce.graph.networks import Network

logger = logging.getLogger()


class VectorNetworkWrapper:
    """
    VectorNetworkWrapper is a class for handling and manipulating geographic network data.
    It provides methods for reading vector data, cleaning it, and setting up network graphs.
    """

    name: str = "project_name"
    region: gpd.GeoDataFrame = None
    crs: CRS = CRS.from_user_input(4326)
    network_dict: dict

    base_network: gpd.GeoDataFrame
    base_graph: nx.MultiGraph

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
                f"A network dictionary is required for creating a {self.__class__.__name__} object."
            )
        if not isinstance(config.get("network"), dict):
            raise ValueError('Config["network"] should be a dictionary')

        self._setup_global(config["project"])
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
            If the value contains a comma, it is split and returned as a list, otherwise the original value is returned.
        """
        if isinstance(value, str) and "," in value:
            return [v for v in value.split(",")]
        else:
            return value

    def _setup_global(self, project_config: dict):
        """
        Sets up project properties based on provided configuration.

        Parameters
        ----------
        project_config : dict
            Project configuration dictionary.
        """
        name = self._parse_ini_value(project_config.get(["name"]))
        region = self._parse_ini_value(project_config.get(["region"], None))
        crs = self._parse_ini_value(project_config.get(["crs"], 4326))
        self.name = name
        self.region = self.read_vector(region)
        self.crs = CRS.from_user_input(crs)

    def _get_network_opt(self, network_config: dict) -> dict:
        """
        Retrieves network options from provided configuration.

        Parameters
        ----------
        network_config : dict
            Network configuration dictionary.

        Returns
        -------
        dict
            Dictionary of network options.
        """
        file = self._parse_ini_value(network_config.get(["primary_file"], None))
        file_id = self._parse_ini_value(
            network_config.get(["file_id"], None)
        )  # Removed trailing space
        file_filter = self._parse_ini_value(network_config.get(["filter"], None))
        file_crs = self._parse_ini_value(network_config.get(["crs"], None))
        is_directed = self._parse_ini_value(network_config.get(["directed"], False))
        return dict(
            file=file,
            file_id=file_id,
            file_filter=file_filter,
            file_crs=file_crs,
            is_directed=is_directed,
        )

    def setup_graph_from_vector(
        self, gdf: gpd.GeoDataFrame, is_directed=False
    ) -> nx.Graph:
        """
        Creates a graph with nodes and edges based on a given GeoDataFrame.

        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            Input geographic data.
        is_directed : bool, optional
            Whether the graph should be directed, by default False.

        Returns
        -------
        nx.Graph
            NetworkX graph object.
        """
        G = nx.DiGraph(crs=self.crs, name=self.name)
        for index, row in gdf.iterrows():
            from_node = row.geometry.coords[0]
            to_node = row.geometry.coords[-1]
            G.add_node(from_node, geometry=Point(from_node))
            G.add_node(to_node, geometry=Point(to_node))
            G.add_edge(from_node, to_node, id=row.index, geometry=row.geometry)

        if is_directed:
            return G
        else:
            return G.to_undirected()

    def setup_network_from_graph(
        self, G: nx.Graph, edge_fid="edge_fid", include_nodes=False, node_fid="node_fid"
    ) -> gpd.GeoDataFrame:
        """
        Sets up network nodes and edges from a given graph.

        Parameters
        ----------
        G : nx.Graph
            Input graph.
        edge_fid : str, optional
            Field id for edges, by default "edge_fid".
        include_nodes : bool, optional
            Whether to include nodes in the out, by default "False"
        node_fid : str, optional
            Field id for nodes, by default "node_fid".

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing edges of the network.
            Or tuple of GeomDataFrames representing edges and nodes of the network if `include_nodes = True`
        """
        nodes, edges = momepy.nx_to_gdf(G, nodeID=node_fid)
        edges[edge_fid] = (
            edges["node_start"].astype(str) + "_" + edges["node_end"].astype(str)
        )
        edges.rename(
            {"node_start": "node_A", "node_end": "node_B"}, axis=1, inplace=True
        )  # FIXME make consistant convention with osm
        if not nodes.crs:
            nodes.crs = self.crs
        if not edges.crs:
            edges.crs = self.crs

        if include_nodes is True:
            return edges, nodes
        else:
            return edges

    def setup_network_from_vector(
        self,
        file: Union[str, Path, List[str, Path]],
        file_crs: Union[int, str],
        is_directed: bool = False,
        **kwargs,
    ) -> Tuple[nx.MultiGraph, gpd.GeoDataFrame]:
        """
        Sets up a network from a given vector file.

        Parameters
        ----------
        file : Union[str, Path, List[str, Path]]
            Path to the vector file or list of paths.
        file_crs : Union[int, str]
            Coordinate reference system for the file.
        is_directed : bool, optional
            Whether the graph is directed, by default "False"
        **kwargs
            Arbitrary keyword arguments.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the network.
        """
        gdf = self.read_vector(fn=file, crs=file_crs)
        gdf = self.clean_vector(
            gdf, explode_and_deduplicate_geometries=True
        )  # TODO maybe move explode_and_deduplicate_geometries to [project] or [cleanup]
        g = self.setup_graph_from_vector(gdf, include_nodes=False)
        network = self.setup_network_from_graph(g, is_directed=is_directed)
        # assign to property
        self.base_graph = nx.MultiGraph(g)
        self.base_network = network
        return self.base_graph, self.base_network

    def read_vector(
        self, fn: Union[str, Path, List[str, Path]], crs: Union[int, str]
    ) -> gpd.GeoDataFrame:
        """
        Reads a vector file or a list of vector files within project region with project crs.

        Parameters
        ----------
        fn : Union[str, Path, List[str, Path]]
            Path to the vector file or list of paths.
        crs : Union[int, str]
            Coordinate reference system for the file. Allow only one crs for all fn.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the vector data.
        """
        gdf = self._read_file(fn)
        if gdf is None:
            logger.info("no file is read.")
            return None

        # set crs and reproject if needed
        if gdf.crs is None and crs is not None:
            gdf = gdf.set_crs(CRS.from_user_input(crs))
            logger.info("setting crs as default EPSG:4326. specify crs if incorrect")

        if self.crs is not None:
            gdf = gdf.to_crs(self.crs)
            logger.info("reproject vector file to project crs")

        # clip for region
        if self.region is not None:
            gdf = gpd.overlay(gdf, self.region, how="intersection", keep_geom_type=True)
            logger.info("clip vector file to project region")

        # validate
        if len(gdf) == 0:
            logger.warning(f"No vector features found within project region")
            return None

        return gdf

    def _read_file(self, fn: Union[str, Path, List[str, Path]]) -> gpd.GeoDataFrame:
        """
        Reads a file or a list of files into a GeoDataFrame.

        Parameters
        ----------
        fn : Union[str, Path, List[str, Path]]
            Path to the file or list of paths.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame representing the data.
        """
        # read file
        if isinstance(fn, str) or isinstance(fn, Path):
            gdf = gpd.read_file(fn)
            logger.info("read vector file.")
        elif isinstance(fn, list):
            gdf = gpd.GeoDataFrame(pd.concat([gpd.read_file(_fn) for _fn in fn]))
            logger.info("read vector files.")
        return gdf

    def clean_vector(
        self, gdf: gpd.GeoDataFrame, explode_and_deduplicate_geometries: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Cleans a GeoDataFrame.
        Parameters
        ----------
        gdf : gpd.GeoDataFrame
            Input GeoDataFrame.
        explode_and_deduplicate_geometries : bool, optional
            Whether to explode and deduplicate geometries, by default True.

        Returns
        -------
        gpd.GeoDataFrame
            Cleaned GeoDataFrame.
        """
        if explode_and_deduplicate_geometries is True:
            gdf = self.explode_and_deduplicate_geometries(gdf)

        return gdf

    def explode_and_deduplicate_geometries(
        self, gpd: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
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
