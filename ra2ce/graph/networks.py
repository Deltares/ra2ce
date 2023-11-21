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
import networkx as nx
import pyproj

from ra2ce.common.io.readers import GraphPickleReader
from ra2ce.graph import networks_utils as nut
from ra2ce.graph.exporters.network_exporter_factory import NetworkExporterFactory
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_wrappers.network_wrapper_factory import NetworkWrapperFactory


class Network:
    """Network in GeoDataFrame or NetworkX format.

    Networks can be created from shapefiles, OSM PBF files, can be downloaded from OSM online or can be loaded from
    feather or gpickle files. Origin-destination nodes can be added.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
    """

    def __init__(self, network_config: NetworkConfigData, files: dict):
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

        # files
        self.files = files

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
        if self._network_config.save_gpkg:
            ods_path = self.output_graph_dir.joinpath(name + ".gpkg")
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

    def _export_network_files(
        self, network: Any, graph_name: str, types_to_export: list[str]
    ):
        _exporter = NetworkExporterFactory()
        _exporter.export(
            network=network,
            basename=graph_name,
            output_dir=self.output_graph_dir,
            export_types=types_to_export,
        )
        self.files[graph_name] = _exporter.get_pickle_path()

    def _get_new_network_and_graph(
        self, export_types: list[str]
    ) -> tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        _base_graph, _network_gdf = NetworkWrapperFactory(
            self._config_data
        ).get_network()

        self.base_graph_crs = _network_gdf.crs
        self.base_network_crs = _network_gdf.crs

        # Set the road lengths to meters for both the base_graph and network_gdf
        # TODO: rename "length" column to "length [m]" to be explicit
        edges_lengths_meters = {
            (e[0], e[1], e[2]): {
                "length": nut.line_length(e[-1]["geometry"], _network_gdf.crs)
            }
            for e in _base_graph.edges.data(keys=True)
        }
        nx.set_edge_attributes(_base_graph, edges_lengths_meters)

        _network_gdf["length"] = _network_gdf["geometry"].apply(
            lambda x: nut.line_length(x, _network_gdf.crs)
        )

        # Save the graph and geodataframe
        self._export_network_files(_base_graph, "base_graph", export_types)
        self._export_network_files(_network_gdf, "base_network", export_types)
        return _base_graph, _network_gdf

    def _get_stored_network_and_graph(
        self, base_graph_filepath: Path, base_network_filepath: Path
    ):
        logging.info(
            "Apparently, you already did create a network with ra2ce earlier. "
            + "Ra2ce will use this: {}".format(base_graph_filepath)
        )

        def check_base_file(file_type: str, file_path: Path):
            if (
                not isinstance(base_graph_filepath, Path)
                or not base_graph_filepath.is_file()
            ):
                raise FileNotFoundError(
                    "No base {} file found at {}.".format(file_type, file_path)
                )

        check_base_file("graph", base_graph_filepath)
        check_base_file("network", base_network_filepath)

        _base_graph = GraphPickleReader().read(base_graph_filepath)
        _network_gdf = gpd.read_feather(base_network_filepath)

        # Assuming the same CRS for both the network and graph
        self.base_graph_crs = _network_gdf.crs
        self.base_network_crs = _network_gdf.crs
        return _base_graph, _network_gdf

    def create(self) -> dict:
        """Handler function with the logic to call the right functions to create a network.

        Returns:
            (dict): A dict of a network (GeoDataFrame) and 1 (base NetworkX graph) or 2 graphs (base NetworkX and OD graph)
        """
        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = (
            ["pickle"] if not self._network_config.save_gpkg else ["pickle", "gpkg"]
        )
        od_graph = None
        base_graph = None
        network_gdf = None

        # For all graph and networks - check if it exists, otherwise, make the graph and/or network.
        if not (self.files["base_graph"] or self.files["base_network"]):
            base_graph, network_gdf = self._get_new_network_and_graph(to_save)
        else:
            base_graph, network_gdf = self._get_stored_network_and_graph(
                self.files["base_graph"], self.files["base_network"]
            )

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
