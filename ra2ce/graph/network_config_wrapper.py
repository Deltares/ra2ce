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
from typing import Optional

from ra2ce.common.configuration.config_wrapper_protocol import ConfigWrapperProtocol
from ra2ce.graph.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.graph.graph_files.graph_files_enum import GraphFilesEnum
from ra2ce.graph.hazard.hazard_overlay import HazardOverlay
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_config_data.network_config_data_validator import (
    NetworkConfigDataValidator,
)
from ra2ce.graph.networks import Network


class NetworkConfigWrapper(ConfigWrapperProtocol):
    ini_file: Path
    config_data: NetworkConfigData
    graph_files: GraphFilesCollection

    def __init__(self) -> None:
        self.ini_file = None
        self.config_data = NetworkConfigData()
        self.graph_files = GraphFilesCollection()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: NetworkConfigData
    ) -> NetworkConfigWrapper:
        """
        Initializes a `NetworkConfig` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (NetworkIniConfigData): Ini data representation.

        Returns:
            NetworkConfig: Initialized instance.
        """
        _new_network_config = cls()
        _new_network_config.ini_file = ini_file
        _new_network_config.config_data = config_data
        if config_data.output_graph_dir and config_data.output_graph_dir.is_dir():
            _new_network_config.graph_files = (
                _new_network_config.get_existent_network_files(
                    config_data.output_graph_dir
                )
            )
        else:
            logging.error(
                f"Graph dir not found. Value provided: {config_data.output_graph_dir}"
            )
        return _new_network_config

    @staticmethod
    def get_existent_network_files(output_graph_dir: Path) -> GraphFilesCollection:
        """Checks if file of graph exist in network folder and adds filename to the graph object"""
        _graph_files = GraphFilesCollection()
        return _graph_files.set_files(output_graph_dir)

    @staticmethod
    def read_graphs_from_config(static_output_dir: Path) -> GraphFilesCollection:
        _graph_files = GraphFilesCollection()
        if not static_output_dir.exists():
            raise ValueError("Path does not exist: {}".format(static_output_dir))
        # Load graphs 
        # TODO (fix): why still read hazard as necessary if analysis of single link redundancy can run without hazard?
        for input_graph in [
            GraphFilesEnum.BASE_GRAPH,
            GraphFilesEnum.BASE_GRAPH_HAZARD,
            GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH,
            GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD,
        ]:
            _graph_files.read_graph(static_output_dir.joinpath(f"{input_graph}.p"))

        # Load networks
        for input_graph in [GraphFilesEnum.BASE_NETWORK, GraphFilesEnum.BASE_NETWORK_HAZARD]
            _graph_files.read_graph(static_output_dir.joinpath(f"{input_graph}.feather"))

        return _graph_files

    def configure(self) -> None:
        self.configure_network()
        self.configure_hazard()

    def configure_network(self) -> None:
        network = Network(self.config_data, self.graph_files)
        self.graph_files = network.create()

    def configure_hazard(self) -> None:
        # Call Hazard Handler (to rework)
        if not self.graph_files.has_graphs():
            self.graph_files = self.read_graphs_from_config(
                self.config_data.static_path.joinpath("output_graph")
            )

        if not self.config_data.hazard.hazard_map:
            return

        # There is a hazard map or multiple hazard maps that should be intersected with the graph.
        hazard = HazardOverlay(self.config_data, self.graph_files)
        self.graph_files = hazard.create()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        _validation_report = NetworkConfigDataValidator(self.config_data).validate()
        return _file_is_valid and _validation_report.is_valid()
