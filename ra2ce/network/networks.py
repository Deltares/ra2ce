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

import copy
import logging
import warnings
from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx
import pandas as pd
import pyproj

from ra2ce.network import networks_utils as nut
from ra2ce.network.exporters.network_exporter_factory import NetworkExporterFactory
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_wrappers.network_wrapper_factory import NetworkWrapperFactory


class Network:
    """Network in GeoDataFrame or NetworkX format.

    Networks can be created from shapefiles, OSM PBF files, can be downloaded from OSM online or can be loaded from
    feather or gpickle files. Origin-destination nodes can be added.

    Attributes:
        config: An object with the configuration details on how to create and adjust the network.
    """

    def __init__(
        self, network_config: NetworkConfigData, graph_files: GraphFilesCollection
    ):
        # General
        self._config_data = network_config
        self.project_name = network_config.project.name
        self.output_graph_dir = network_config.output_graph_dir
        if not self.output_graph_dir.is_dir():
            self.output_graph_dir.mkdir(parents=True)

        # Network
        self._network_dir = network_config.network_dir
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
        self.region = _origins_destinations.region
        self.region_var = _origins_destinations.region_var

        # graph files
        self.graph_files = graph_files

    def add_od_nodes(self, graph: nx.Graph, crs: pyproj.CRS) -> nx.Graph:
        """Adds origins and destinations nodes from shapefiles to the graph.

        Args:
            graph (NetworkX graph): the NetworkX graph to which OD nodes should be added
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            graph (NetworkX graph): the NetworkX graph with OD nodes
        """
        from ra2ce.network.origins_destinations import (
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

        (ods, graph) = add_od_nodes(ods, graph, crs, self.od_category)
        ods.crs = crs

        # Save the OD pairs (GeoDataFrame) as pickle
        ods.to_feather(self.output_graph_dir.joinpath(name + ".feather"), index=False)
        logging.info(f"Saved {name + '.feather'} in {self.output_graph_dir}.")

        # Save the OD pairs (GeoDataFrame) as shapefile
        if self._network_config.save_gpkg:
            ods_path = self.output_graph_dir.joinpath(name + ".gpkg")
            ods.to_file(ods_path, index=False)
            logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        return graph

    def generate_origins_from_raster(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        from ra2ce.network.origins_destinations import origins_from_raster

        out_fn = origins_from_raster(
            self._network_dir,
            self._network_config.polygon,
            self.origins,
        )

        return out_fn

    def _export_network_files(
        self,
        network: nx.MultiGraph | gpd.GeoDataFrame,
        graph_type: str,
        types_to_export: list[str],
    ):
        _exporter = NetworkExporterFactory()
        _exporter.export(
            network=network,
            basename=graph_type,
            output_dir=self.output_graph_dir,
            export_types=types_to_export,
        )
        self.graph_files.set_file(_exporter.get_pickle_path())
        self.graph_files.set_graph(graph_type, network)

    def _include_attributes(self, attributes: list, graph: nx.Graph) -> nx.Graph:
        # If required_attributes are provided, check if all edges already have them
        if attributes and all(
            all(attr in edge_data for attr in attributes)
            for _, _, edge_data in graph.edges(data=True)
        ):
            # If all required attributes are present, return the original graph
            return graph
        graph = nut.add_x_y_to_nodes(graph)
        _, gdf_edges = osmnx.graph_to_gdfs(graph)
        updated_graph = copy.deepcopy(graph)
        for attribute in attributes:
            if attribute in gdf_edges.columns:
                attribute_values_gdf = gdf_edges[attribute]
                for (u, v, key), attribute_values in attribute_values_gdf.items():
                    updated_graph[u][v][key][attribute] = attribute_values
        return updated_graph

    def _get_new_network_and_graph(self, export_types: list[str]) -> None:
        """
        TODO: This method should be relying on a generic definition of a network result
        from `.get_network`. This means, instead of getting `_base_graph, _network_gdf`
        we get a generic `_ra2ce_network_wrapper` from which can later on just do a
        `.simplify_network` or `.add_eges`, etc. using inheritance.
        """

        _base_graph, _network_gdf = NetworkWrapperFactory(
            self._config_data
        ).get_network()

        self.base_graph_crs = _network_gdf.crs
        self.base_network_crs = _network_gdf.crs

        _base_graph = self._include_attributes(
            attributes=["avgspeed", "bridge", "tunnel"], graph=_base_graph
        )

        # Save the graph and geodataframe
        self._export_network_files(_base_graph, "base_graph", export_types)
        self._export_network_files(_network_gdf, "base_network", export_types)

    def _get_stored_network_and_graph(self) -> None:
        base_graph_filepath = self.graph_files.base_graph.file
        base_network_filepath = self.graph_files.base_network.file

        logging.info(
            "Apparently, you already did create a network with ra2ce earlier. "
            + "Ra2ce will use this: %s",
            base_graph_filepath,
        )

        def get_graph(
            file_type: str, file_path: Path | None
        ) -> nx.MultiGraph | gpd.GeoDataFrame:
            graph = self.graph_files.get_graph(file_type)
            if graph is None:
                raise FileNotFoundError(
                    "No base {} file found at {}.".format(file_type, file_path)
                )
            return graph

        _base_graph = get_graph("base_graph", base_graph_filepath)
        _network_gdf = get_graph("base_network", base_network_filepath)

        # Assuming the same CRS for both the network and graph
        self.base_graph_crs = _network_gdf.crs
        self.base_network_crs = _network_gdf.crs

    def create(self) -> GraphFilesCollection:
        """Handler function with the logic to call the right functions to create a network.

        Returns:
            (GraphFilesCollection): A collection of a network (GeoDataFrame) and 1 (base NetworkX graph) or 2 graphs (base NetworkX and OD graph)
        """
        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = (
            ["pickle"] if not self._network_config.save_gpkg else ["pickle", "gpkg"]
        )

        # For all graph and networks - check if it exists, otherwise, make the graph and/or network.
        if not (self.graph_files.base_graph.file or self.graph_files.base_network.file):
            self._get_new_network_and_graph(to_save)
        else:
            self._get_stored_network_and_graph()

        # create origins destinations graph
        if (
            (self.origins)
            and (self.destinations)
            and not self.graph_files.origins_destinations_graph.file
        ):
            # fetch the base graph
            base_graph = self.graph_files.base_graph.get_graph()
            # adding OD nodes
            if self.origins.suffix == ".tif":
                self.origins = self.generate_origins_from_raster()
            od_graph = self.add_od_nodes(base_graph, self.base_graph_crs)
            self._export_network_files(od_graph, "origins_destinations_graph", to_save)

        return self.graph_files
