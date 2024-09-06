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

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.analysis_config_data_validator import (
    AnalysisConfigDataValidator,
)
from ra2ce.common.configuration.config_wrapper_protocol import ConfigWrapperProtocol
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper


class AnalysisConfigWrapper(ConfigWrapperProtocol):
    ini_file: Path
    config_data: AnalysisConfigData
    graph_files: GraphFilesCollection

    def __init__(self) -> None:
        self.ini_file = None
        self.config_data = AnalysisConfigData()
        self.graph_files = GraphFilesCollection()

    def initialize_output_dirs(self) -> None:
        """
        #Initializes the required output directories for a Ra2ce analysis.
        """
        # Create the output folders
        for a in self.config_data.analyses:
            output_path = self.config_data.output_path.joinpath(a.analysis.config_value)
            output_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_data_with_network(
        cls,
        ini_file: Path,
        config_data: AnalysisConfigData,
        network_config: NetworkConfigWrapper,
    ) -> AnalysisConfigWrapper:
        """
        Initializes an `AnalysisConfigWrapper` with the given parameters,
        with network_config as input from the network phase.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.
            network_config (NetworkConfig): Network configuration to be used on this analysis.

        Raises:
            FileNotFoundError: When the provided `ini file` cannot be found.

        Returns:
            AnalysisConfigWrapper: Initialized instance.
        """
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        _new_analysis = cls()
        _new_analysis.ini_file = ini_file
        _new_analysis.config_data = config_data

        if not isinstance(network_config, NetworkConfigWrapper):
            raise ValueError("No valid network config provided.")
        _new_analysis.config_data.network = network_config.config_data.network
        _new_analysis.config_data.origins_destinations = (
            network_config.config_data.origins_destinations
        )
        _new_analysis.config_data.aggregate_wl = (
            network_config.config_data.hazard.aggregate_wl
        )
        # Graphs are retrieved from the already configured object
        _new_analysis.graph_files = network_config.graph_files

        return _new_analysis

    def configure(self) -> None:
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        return AnalysisConfigDataValidator(self.config_data).validate().is_valid()
