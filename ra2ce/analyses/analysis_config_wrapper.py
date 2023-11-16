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

from ra2ce.analyses.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator import (
    AnalysisConfigDataValidator,
)
from ra2ce.common.configuration.config_wrapper_protocol import ConfigWrapperProtocol
from ra2ce.graph.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper


class AnalysisConfigWrapper(ConfigWrapperProtocol):
    ini_file: Path
    config_data: AnalysisConfigData
    graphs: Optional[dict]
    _network_config: Optional[NetworkConfigWrapper]

    def __init__(self) -> None:
        self.ini_file = None
        self.config_data = AnalysisConfigData()
        self.graphs = None
        self._network_config = None

    @staticmethod
    def get_network_root_dir(filepath: Path) -> Path:
        return filepath.parent.parent

    @staticmethod
    def get_data_output(ini_file: Path) -> Optional[Path]:
        _root_path = AnalysisConfigWrapper.get_network_root_dir(ini_file)
        _project_name = ini_file.parent.name
        return _root_path.joinpath(_project_name, "output")

    @property
    def root_dir(self) -> Path:
        return self.get_network_root_dir(self.ini_file)

    def initialize_output_dirs(self) -> None:
        """
        #Initializes the required output directories for a Ra2ce analysis.
        """
        # Create the output folders
        for a in self.config_data.analyses:
            output_path = self.config_data.output_path.joinpath(a.analysis)
            output_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisConfigData
    ) -> AnalysisConfigWrapper:
        """
        Initializes an `AnalysisConfigWrapper` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.

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
        return _new_analysis

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
        _new_analysis = cls.from_data(ini_file, config_data)
        _new_analysis._network_config = network_config
        return _new_analysis

    @classmethod
    def from_data_without_network(
        cls,
        ini_file: Path,
        config_data: AnalysisConfigData,
    ) -> AnalysisConfigWrapper:
        """
        Initializes an `AnalysisConfigWrapper` with the given parameters,
        without a given network_config.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.

        Raises:
            FileNotFoundError: When the provided `ini file` cannot be found.

        Returns:
            AnalysisConfigWrapper: Initialized instance.
        """
        _new_analysis = cls.from_data(ini_file, config_data)
        _static_dir = _new_analysis.config_data.static_path
        if _static_dir.is_dir():
            config_data.files = NetworkConfigWrapper._get_existent_network_files(
                _static_dir / "output_graph"
            )
        else:
            logging.error(f"Static dir not found. Value provided: {_static_dir}")
        _new_analysis.config_data.files = config_data.files
        return _new_analysis

    def configure(self) -> None:
        # If no network config provided, try reading it from the output folder
        if not self._network_config:
            self._network_config = NetworkConfigWrapper()
            _output_network_ini_file = self.config_data.output_path.joinpath(
                "network.ini"
            )
            self._network_config.config_data = NetworkConfigDataReader().read(
                _output_network_ini_file
            )
        else:
            # When Network is present the graphs are retrieved from the already configured object.
            self.graphs = self._network_config.graphs
            self.config_data.files = self._network_config.files
            self.config_data.network = self._network_config.config_data.network
            self.config_data.origins_destinations = (
                self._network_config.config_data.origins_destinations
            )

        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        _validation_report = AnalysisConfigDataValidator(self.config_data).validate()
        return _file_is_valid and _validation_report.is_valid()
