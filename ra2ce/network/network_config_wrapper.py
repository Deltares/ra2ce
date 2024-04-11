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

from pathlib import Path

from ra2ce.common.configuration.config_wrapper_protocol import ConfigWrapperProtocol
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.hazard.hazard_overlay import HazardOverlay
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_data.network_config_data_validator import (
    NetworkConfigDataValidator,
)
from ra2ce.network.networks import Network


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
        if config_data.output_graph_dir:
            if config_data.output_graph_dir.is_dir():
                _new_network_config.graph_files = (
                    _new_network_config.read_graphs_from_config(
                        config_data.output_graph_dir
                    )
                )
            else:
                config_data.output_graph_dir.mkdir(parents=True)
        return _new_network_config

    @staticmethod
    def read_graphs_from_config(static_output_dir: Path) -> GraphFilesCollection:
        if not static_output_dir.exists():
            raise ValueError("Path does not exist: {}".format(static_output_dir))
        # Load graphs
        _graph_files = GraphFilesCollection.set_files(static_output_dir)

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
        return NetworkConfigDataValidator(self.config_data).validate().is_valid()
