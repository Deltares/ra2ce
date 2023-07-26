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
import math
import os
from pathlib import Path
from typing import Any, List, Tuple

import geopandas as gpd
import networkx as nx
import pandas as pd
import pyproj
import momepy
from shapely.geometry import MultiLineString

from ra2ce.common.io.readers import GraphPickleReader
from ra2ce.graph import networks_utils as nut
from ra2ce.graph.exporters.json_exporter import JsonExporter
from ra2ce.graph.exporters.network_exporter_factory import NetworkExporterFactory
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.osm_network_wrapper.osm_network_wrapper import OsmNetworkWrapper
from ra2ce.graph.segmentation import Segmentation
from ra2ce.graph.vector_network_wrapper import VectorNetworkWrapper


class Network:
    """Network in GeoDataFrame or NetworkX format.

    Networks can be created from shapefiles, OSM PBF files, can be downloaded from OSM online or can be loaded from
    feather or gpickle files. Origin-destination nodes can be added.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
    """

    output_graph_dir: Path
    files: dict
    base_graph_crs: Any
    base_network_crs: Any

    def __init__(self, network_config: NetworkConfigData, files: dict):
        # General
        self.project_name = network_config.project.name
        self.output_graph_dir = network_config.static_path.joinpath("output_graph")
        if not self.output_graph_dir.is_dir():
            self.output_graph_dir.mkdir(parents=True)

        # Network
        self._network_dir = network_config.static_path.joinpath("network")
        self.base_graph_crs = None  # Initiate variable
        self.base_network_crs = None  # Initiate variable

        self._network_config = network_config.network

        # Origins and destinations
        _origins_destinations = network_config.origins_destinations
        self.origins = _origins_destinations.origins
        self.destinations = _origins_destinations.destinations
        self.origins_names = _origins_destinations.origins_names
        self.destinations_names = _origins_destinations.destinations_names
        self.id_name_origin_destination = (
            _origins_destinations.id_name_origin_destination
        )
        self.origin_count = _origins_destinations.origin_count
        self.od_category = _origins_destinations.category
        self.region = (
            None
            if not _origins_destinations.region
            else network_config.static_path.joinpath(
                "network", _origins_destinations.region
            )
        )
        self.region_var = _origins_destinations.region_var

        # Cleanup
        self._cleanup = network_config.cleanup

        # files
        self.files = files

    def _setup_cleanup_options(self, opt: dict):
        # TODO: remove the attributes once cleanup function is used
        self.cleanup = opt.get("cleanup", False)
        self.snapping = opt.get("snapping_threshold", None)
        self.segmentation_length = opt.get("segmentation_length", None)
        self.merge_lines = opt.get("merge_lines", None)
        self.merge_on_id = opt.get("merge_on_id", None)
        self.cut_at_intersections = opt.get("cut_at_intersections", None)

    def network_shp(
        self, crs: int = 4326
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a (graph) network from a shapefile.

        Returns the same geometries for the network (GeoDataFrame) as for the graph (NetworkX graph), because
        it is assumed that the user wants to keep the same geometries as their shapefile input.

        Args:
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            graph_complex (NetworkX graph): The resulting graph.
            edges_complex (GeoDataFrame): The resulting network.
        """
        # Make a pyproj CRS from the EPSG code
        crs = pyproj.CRS.from_user_input(crs)

        lines = self.read_merge_shp(crs)

        logging.info(
            "Function [read_merge_shp]: executed with {} {}".format(
                self._network_config.primary_file,
                self._network_config.diversion_file,
            )
        )

        # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
        # The list of fid's is reduced by the fid's that are not anymore in the merged lines
        if self._cleanup.merge_lines:
            aadt_names = []
            edges, lines_merged = nut.merge_lines_automatic(
                lines, self._network_config.file_id, aadt_names, crs
            )
            logging.info(
                "Function [merge_lines_automatic]: executed with properties {}".format(
                    list(edges.columns)
                )
            )
        else:
            edges, lines_merged = lines, gpd.GeoDataFrame()

        edges, id_name = nut.gdf_check_create_unique_ids(
            edges, self._network_config.file_id
        )

        if self._cleanup.snapping_threshold:
            edges = nut.snap_endpoints_lines(
                edges, self._cleanup.snapping_threshold, id_name, crs
            )
            logging.info(
                "Function [snap_endpoints_lines]: executed with threshold = {}".format(
                    self._cleanup.snapping_threshold
                )
            )

        # merge merged lines if there are any merged lines
        if not lines_merged.empty:
            # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
            lines_merged.set_geometry(
                col="geometry", inplace=True
            )  # To ensure the object is a GeoDataFrame and not a Series
            lines_merged.to_file(
                os.path.join(
                    self.output_graph_dir,
                    "{}_lines_that_merged.shp".format(self.project_name),
                )
            )
            logging.info(
                "Function [edges_to_shp]: saved at {}".format(
                    os.path.join(
                        self.output_graph_dir,
                        "{}_lines_that_merged".format(self.project_name),
                    )
                )
            )

        # Get the unique points at the end of lines and at intersections to create nodes
        nodes = nut.create_nodes(edges, crs, self._cleanup.cut_at_intersections)
        logging.info("Function [create_nodes]: executed")

        edges = nut.cut_lines(
            edges, nodes, id_name, tolerance=0.00001, crs_=crs
        )  ## PAY ATTENTION TO THE TOLERANCE, THE UNIT IS DEGREES
        logging.info("Function [cut_lines]: executed")

        if not edges.crs:
            edges.crs = crs

        # create tuples from the adjecent nodes and add as column in geodataframe
        edges_complex = nut.join_nodes_edges(nodes, edges, id_name)
        edges_complex.crs = crs  # set the right CRS
        edges_complex.dropna(subset=["node_A", "node_B"], inplace=True)

        assert (
            edges_complex["node_A"].isnull().sum() == 0
        ), "Some edges cannot be assigned nodes, please check your input shapefile."
        assert (
            edges_complex["node_B"].isnull().sum() == 0
        ), "Some edges cannot be assigned nodes, please check your input shapefile."

        # Create networkx graph from geodataframe
        graph_complex = nut.graph_from_gdf(edges_complex, nodes, node_id="node_fid")
        logging.info("Function [graph_from_gdf]: executed")

        if not math.isnan(self._cleanup.segmentation_length):
            edges_complex = Segmentation(
                edges_complex, self._cleanup.segmentation_length
            )
            edges_complex = edges_complex.apply_segmentation()
            if edges_complex.crs is None:  # The CRS might have dissapeared.
                edges_complex.crs = crs  # set the right CRS

        self.base_graph_crs = pyproj.CRS.from_user_input(crs)
        self.base_network_crs = pyproj.CRS.from_user_input(crs)

        # Exporting complex graph because the shapefile should be kept the same as much as possible.
        return graph_complex, edges_complex

    def network_cleanshp(self) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a (graph) network from a clean shapefile (primary_file - no further advance cleanup is needed)

        Returns the same geometries for the network (GeoDataFrame) as for the graph (NetworkX graph), because
        it is assumed that the user wants to keep the same geometries as their shapefile input.

        Returns:
            graph_complex (NetworkX graph): The resulting graph.
            edges_complex (GeoDataFrame): The resulting network.
        """
        # initialise vector network wrapper
        vector_network_wrapper = VectorNetworkWrapper(config=self.config)

        # setup network using the wrapper
        (
            graph_complex,
            edges_complex,
        ) = vector_network_wrapper.setup_network_from_vector()

        # Set the CRS of the graph and network to wrapper crs
        self.base_graph_crs = vector_network_wrapper.crs
        self.base_network_crs = vector_network_wrapper.crs

        return graph_complex, edges_complex

    def _export_linking_tables(self, linking_tables: List[Any]) -> None:
        _exporter = JsonExporter()
        _exporter.export(
            self.output_graph_dir.joinpath("simple_to_complex.json"), linking_tables[0]
        )
        _exporter.export(
            self.output_graph_dir.joinpath("complex_to_simple.json"), linking_tables[1]
        )

    def network_trails_import(
        self, crs: int = 4326
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a network which has been prepared in the TRAILS package

        #Todo: we might later simply import the whole trails code as a package, and directly use these functions
        #Todo: because TRAILS is still in beta version we better wait with that untill the first stable version is
        # released

        Returns:
            graph_simple (NetworkX graph): Simplified graph (for use in the indirect analyses).
            complex_edges (GeoDataFrame): Complex graph (for use in the direct analyses).
        """

        logging.info(
            "TRAILS importer: Reads the provided primary edge file: {}, assumes there also is a_nodes file".format(
                self._network_config.primary_file
            )
        )

        logging.warning(
            "Any coordinate projection information in the feather file will be overwritten (with default WGS84)"
        )
        # Make a pyproj CRS from the EPSG code
        crs = pyproj.CRS.from_user_input(crs)

        edge_file = self._network_dir.joinpath(self._network_config.primary_file)
        edges = gpd.read_feather(edge_file)
        edges = edges.set_crs(crs)

        corresponding_node_file = self._network_dir.joinpath(
            self._network_config.primary_file.replace("edges", "nodes")
        )
        assert (
            corresponding_node_file.exists()
        ), "The node file could not be found while importing from TRAILS"
        nodes = gpd.read_feather(corresponding_node_file)
        nodes = nodes.set_crs(crs)
        # nodes = pd.read_pickle(
        #     corresponding_node_file
        # )  # Todo: Throw exception if nodes file is not present

        logging.info("TRAILS importer: start generating graph")
        # tempfix to rename columns
        edges = edges.rename({"from_id": "node_A", "to_id": "node_B"}, axis="columns")
        node_id = "id"
        graph_simple = nut.graph_from_gdf(edges, nodes, name="network", node_id=node_id)

        logging.info("TRAILS importer: graph generating was succesfull.")
        logging.warning(
            "RA2CE will not clean-up your graph, assuming that it is already done in TRAILS"
        )

        if self._cleanup.segmentation_length:
            logging.info("TRAILS importer: start segmentating graph")
            to_segment = Segmentation(edges, self._cleanup.segmentation_length)
            edges_simple_segmented = to_segment.apply_segmentation()
            if edges_simple_segmented.crs is None:  # The CRS might have dissapeared.
                edges_simple_segmented.crs = edges.crs  # set the right CRS
                edges_complex = edges_simple_segmented

        else:
            edges_complex = edges

        graph_complex = graph_simple  # NOTE THAT DIFFERENCE
        # BETWEEN SIMPLE AND COMPLEX DOES NOT EXIST WHEN IMPORTING WITH TRAILS

        # Todo: better control over metadata in trails
        # Todo: better control over where things are saved in the pipeline

        return graph_complex, edges_complex

    def network_osm_download(self) -> tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """
        Creates a network from a polygon by downloading via the OSM API in the extent of the polygon.

        Returns:
            tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]: Tuple of Simplified graph (for use in the indirect analyses) and Complex graph (for use in the direct analyses).
        """
        osm_network = OsmNetworkWrapper(
            network_type=self._network_config.network_type,
            road_types=self._network_config.road_types,
            graph_crs="",
            polygon_path=self._network_dir.joinpath(self._network_config.polygon),
        )
        graph_complex = osm_network.get_clean_graph_from_osm()

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

        # If the user wants to use undirected graphs, turn into an undirected graph (default).
        if not self._network_config.directed:
            if type(graph_simple) == nx.classes.multidigraph.MultiDiGraph:
                graph_simple = graph_simple.to_undirected()

        # No segmentation required, the non-simplified road segments from OSM are already small enough

        self.base_graph_crs = pyproj.CRS.from_user_input(
            "EPSG:4326"
        )  # Graphs from OSM download are always in this CRS.
        self.base_network_crs = pyproj.CRS.from_user_input(
            "EPSG:4326"
        )  # Graphs from OSM download are always in this CRS.

        return graph_simple, edges_complex

    def add_od_nodes(
        self, graph: nx.classes.graph.Graph, crs: pyproj.CRS
    ) -> nx.classes.graph.Graph:
        """Adds origins and destinations nodes from shapefiles to the graph.

        Args:
            graph (NetworkX graph): the NetworkX graph to which OD nodes should be added
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            graph (NetworkX graph): the NetworkX graph with OD nodes
        """
        from ra2ce.graph.origins_destinations import (
            add_od_nodes,
            read_origin_destination_files,
        )

        name = "origin_destination_table"

        # Add the origin/destination nodes to the network
        ods = read_origin_destination_files(
            str(self.origins),
            self.origins_names,
            str(self.destinations),
            self.destinations_names,
            self.id_name_origin_destination,
            self.origin_count,
            crs,
            self.od_category,
            self.region if self.region else "",
            self.region_var,
        )

        ods, graph = add_od_nodes(ods, graph, crs, self.od_category)
        ods.crs = crs

        # Save the OD pairs (GeoDataFrame) as pickle
        ods.to_feather(self.output_graph_dir.joinpath(name + ".feather"), index=False)
        logging.info(f"Saved {name + '.feather'} in {self.output_graph_dir}.")

        # Save the OD pairs (GeoDataFrame) as shapefile
        if self._network_config.save_shp:
            ods_path = self.output_graph_dir.joinpath(name + ".shp")
            ods.to_file(ods_path, index=False)
            logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        return graph

    def generate_origins_from_raster(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        from ra2ce.graph.origins_destinations import origins_from_raster

        out_fn = origins_from_raster(
            self._network_dir,
            self._network_config.polygon,
            self.origins,
        )

        return out_fn

    def read_merge_shp(self, crs_: pyproj.CRS) -> gpd.GeoDataFrame:
        """Imports shapefile(s) and saves attributes in a pandas dataframe.

        Args:
            crs_ (int): the EPSG number of the coordinate reference system that is used
        Returns:
            lines (list of shapely LineStrings): full list of linestrings
            properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
        """

        # read shapefiles and add to list with path
        def get_shp_paths(shp_str: str) -> Path:
            return self._network_dir.joinpath(shp_str)

        shapefiles_analysis = list(
            map(get_shp_paths, self._network_config.primary_file.split(","))
        )
        shapefiles_diversion = list(
            map(get_shp_paths, self._network_config.diversion_file.split(","))
        )

        # concatenate all shapefile into one geodataframe and set analysis to 1 or 0 for diversions
        lines = [gpd.read_file(shp) for shp in shapefiles_analysis]

        if self._network_config.diversion_file:
            lines.extend(
                [
                    nut.check_crs_gdf(gpd.read_file(shp), crs_)
                    for shp in shapefiles_diversion
                ]
            )
        lines = pd.concat(lines)

        lines.crs = crs_

        # Check if there are any multilinestrings and convert them to linestrings.
        if lines["geometry"].apply(lambda row: isinstance(row, MultiLineString)).any():
            mls_idx = lines.loc[
                lines["geometry"].apply(lambda row: isinstance(row, MultiLineString))
            ].index
            for idx in mls_idx:
                # Multilinestrings to linestrings
                new_rows_geoms = list(lines.iloc[idx]["geometry"].geoms)
                for nrg in new_rows_geoms:
                    dict_attributes = dict(lines.iloc[idx])
                    dict_attributes["geometry"] = nrg
                    lines.loc[max(lines.index) + 1] = dict_attributes

            lines = lines.drop(labels=mls_idx, axis=0)

        # append the length of the road stretches
        lines["length"] = lines["geometry"].apply(lambda x: nut.line_length(x, crs_))

        logging.info(
            "Shapefile(s) loaded with attributes: {}.".format(
                list(lines.columns.values)
            )
        )  # fill in parameter names

        return lines

    def get_avg_speed(
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
        else:
            logging.info(
                "No attributes found in the graph to estimate average speed per network segment."
            )
            return original_graph

    def _export_network_files(
        self, network: Any, graph_name: str, types_to_export: List[str]
    ):
        _exporter = NetworkExporterFactory()
        _exporter.export(
            network=network,
            basename=graph_name,
            output_dir=self.output_graph_dir,
            export_types=types_to_export,
        )
        self.files[graph_name] = _exporter.get_pickle_path()

    def create(self) -> dict:
        """Handler function with the logic to call the right functions to create a network.

        Returns:
            (dict): A dict of a network (GeoDataFrame) and 1 (base NetworkX graph) or 2 graphs (base NetworkX and OD graph)
        """
        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = ["pickle"] if not self._network_config.save_shp else ["pickle", "shp"]
        od_graph = None
        base_graph = None
        network_gdf = None

        # For all graph and networks - check if it exists, otherwise, make the graph and/or network.
        if not (self.files["base_graph"] or self.files["base_network"]):
            # Create the network from the network source
            if self._network_config.source == "shapefile":
                logging.info("Start creating a network from the submitted shapefile.")
                if self.cleanup:
                    base_graph, network_gdf = self.network_shp()
                else:
                    base_graph, network_gdf = self.network_cleanshp()

            elif self._network_config.source == "OSM PBF":
                logging.info(
                    """The original OSM PBF import is no longer supported. 
                                Instead, the beta version of package TRAILS is used. 
                                First stable release of TRAILS is expected in 2023."""
                )

                # base_graph, network_gdf = self.network_osm_pbf() #The old approach is depreciated
                base_graph, network_gdf = self.network_trails_import()

                self.base_network_crs = network_gdf.crs

            elif self._network_config.source == "OSM download":
                logging.info("Start downloading a network from OSM.")
                base_graph, network_gdf = self.network_osm_download()

            elif self._network_config.source == "pickle":
                logging.info("Start importing a network from pickle")
                base_graph = GraphPickleReader().read(
                    self.output_graph_dir.joinpath("base_graph.p")
                )
                network_gdf = gpd.read_feather(
                    self.output_graph_dir.joinpath("base_network.feather")
                )

                # Assuming the same CRS for both the network and graph
                self.base_graph_crs = pyproj.CRS.from_user_input(network_gdf.crs)
                self.base_network_crs = pyproj.CRS.from_user_input(network_gdf.crs)

            if self._network_config.source == "OSM download":
                # Graph & Network from OSM download
                # Check if all geometries between nodes are there, if not, add them as a straight line.
                base_graph = nut.add_missing_geoms_graph(
                    base_graph, geom_name="geometry"
                )

            # Set the road lengths to meters for both the base_graph and network_gdf
            # TODO: rename "length" column to "length [m]" to be explicit
            edges_lengths_meters = {
                (e[0], e[1], e[2]): {
                    "length": nut.line_length(e[-1]["geometry"], self.base_graph_crs)
                }
                for e in base_graph.edges.data(keys=True)
            }
            nx.set_edge_attributes(base_graph, edges_lengths_meters)

            network_gdf["length"] = network_gdf["geometry"].apply(
                lambda x: nut.line_length(x, self.base_network_crs)
            )

            if self._network_config.source == "OSM download":
                base_graph = self.get_avg_speed(base_graph)

            # Save the graph and geodataframe
            self._export_network_files(base_graph, "base_graph", to_save)
            self._export_network_files(network_gdf, "base_network", to_save)
        else:
            logging.info(
                "Apparently, you already did create a network with ra2ce earlier. "
                + "Ra2ce will use this: {}".format(self.files["base_graph"])
            )

            if self.files["base_graph"] is not None:
                base_graph = GraphPickleReader().read(self.files["base_graph"])
            else:
                base_graph = None

            if self.files["base_network"] is not None:
                network_gdf = gpd.read_feather(self.files["base_network"])
            else:
                network_gdf = None

            # Assuming the same CRS for both the network and graph
            self.base_graph_crs = pyproj.CRS.from_user_input(network_gdf.crs)
            self.base_network_crs = pyproj.CRS.from_user_input(network_gdf.crs)

        # create origins destinations graph
        if (
            (self.origins)
            and (self.destinations)
            and not self.files["origins_destinations_graph"]
        ):
            # reading the base graphs
            if self.files["base_graph"] and base_graph:
                base_graph = GraphPickleReader().read(self.files["base_graph"])
            # adding OD nodes
            if self.origins.suffix == ".tif":
                self.origins = self.generate_origins_from_raster()
            od_graph = self.add_od_nodes(base_graph, self.base_graph_crs)
            self._export_network_files(od_graph, "origins_destinations_graph", to_save)

        return {
            "base_graph": base_graph,
            "base_network": network_gdf,
            "origins_destinations_graph": od_graph,
        }
