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
from typing import Optional

from ra2ce.analyses.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_with_network import (
    AnalysisConfigDataValidatorWithNetwork,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper


class AnalysisConfigWrapperWithNetwork(AnalysisConfigWrapperBase):
    _network_config: NetworkConfigWrapper

    def __init__(self) -> None:
        self.config_data = AnalysisConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisConfigData
    ) -> AnalysisConfigWrapperWithNetwork:
        """
        Initializes an `AnalysisWithNetworkConfiguration` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.

        Raises:
            FileNotFoundError: When the provided `ini file` cannot be found.

        Returns:
            AnalysisWithNetworkConfiguration: Initialized instance.
        """
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        _new_analysis = cls()
        _new_analysis.ini_file = ini_file
        _new_analysis.config_data = config_data
        return _new_analysis

    @classmethod
    def from_data_with_network(
        cls,
        ini_file: Path,
        config_data: AnalysisConfigData,
        network_config: Optional[NetworkConfigWrapper],
    ) -> AnalysisConfigWrapperWithNetwork:
        """
        Initializes this class with a network_configuration.

        Args:
            ini_file (Path): Ini file containing the data from the config_data.
            config_data (AnalysisIniConfigData): Ini data representation.
            network_config (NetworkConfig): Network configuration to be used on this analysis.

        Returns:
            AnalysisWithNetworkConfiguration: Created instance.
        """
        _new_analysis = cls.from_data(ini_file, config_data)
        _new_analysis._network_config = network_config
        return _new_analysis

    def configure(self) -> None:
        self.config_data.files = self._network_config.files
        self.config_data.network = self._network_config.config_data.network
        self.config_data.origins_destinations = (
            self._network_config.config_data.origins_destinations
        )

        # When Network is present the graphs are retrieved from the already configured object.
        self.graphs = self._network_config.graphs
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        _validation_report = AnalysisConfigDataValidatorWithNetwork(
            self.config_data
        ).validate()
        return _file_is_valid and _validation_report.is_valid()
