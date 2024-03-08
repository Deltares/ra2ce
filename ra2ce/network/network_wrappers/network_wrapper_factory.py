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

import geopandas as gpd
from geopandas import GeoDataFrame
from networkx import MultiGraph

from ra2ce.common.io.readers import GraphPickleReader
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_network_wrapper import (
    OsmNetworkWrapper,
)
from ra2ce.network.network_wrappers.shp_network_wrapper import ShpNetworkWrapper
from ra2ce.network.network_wrappers.trails_network_wrapper import TrailsNetworkWrapper
from ra2ce.network.network_wrappers.vector_network_wrapper import VectorNetworkWrapper


class NetworkWrapperFactory(NetworkWrapperProtocol):
    def __init__(self, config_data: NetworkConfigData) -> None:
        self._config_data = config_data

    def _any_cleanup_enabled(self) -> bool:
        _cleanup = self._config_data.cleanup
        return (
            _cleanup.snapping_threshold
            or _cleanup.pruning_threshold
            or _cleanup.merge_lines
            or _cleanup.cut_at_intersections
        )

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        logging.info("Start creating a network from the submitted shapefile.")
        source = self._config_data.network.source
        if source == SourceEnum.SHAPEFILE:
            if self._any_cleanup_enabled():
                return ShpNetworkWrapper(self._config_data).get_network()
            return VectorNetworkWrapper(self._config_data).get_network()
        elif source == SourceEnum.OSB_BPF:
            return TrailsNetworkWrapper(self._config_data).get_network()
        elif source == SourceEnum.OSM_DOWNLOAD:
            return OsmNetworkWrapper(self._config_data).get_network()
        elif source == SourceEnum.PICKLE:
            logging.info("Start importing a network from pickle")
            base_graph = GraphPickleReader().read(
                self._config_data.output_graph_dir.joinpath("base_graph.p")
            )
            network_gdf = gpd.read_feather(
                self._config_data.output_graph_dir.joinpath("base_network.feather")
            )
            return base_graph, network_gdf
        raise ValueError(f"Source {source} is not supported.")
