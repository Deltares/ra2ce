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
import shutil
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper


class ConfigFactory:
    @staticmethod
    def get_config_wrapper(
        network_ini: Optional[Path], analysis_ini: Optional[Path]
    ) -> ConfigWrapper:
        """
        Generates a `ConfigWrapper` containing the DataObjectModel representations of the given network and analysis ini files.

        Args:
            network_ini (Path): Path to the  `network.ini` file.
            analysis_ini (Path): Path to the `analysis.ini` file.

        Returns:
            ConfigWrapper: Instantiated `ConfigWrapper`.
        """
        _input_config = ConfigWrapper()
        _input_config.network_config = ConfigFactory.get_network_config_data(
            network_ini
        )
        _input_config.analysis_config = ConfigFactory.get_analysis_config_data(
            analysis_ini, _input_config.network_config
        )
        return _input_config

    @staticmethod
    def get_network_config_data(network_ini: Path) -> Optional[NetworkConfigWrapper]:
        if not network_ini:
            return None
        _network_config = NetworkConfigDataReader().read(network_ini)
        # Copy the network ini file to the output directory.
        if not _network_config.output_path.exists():
            _network_config.output_path.mkdir(parents=True)
        _output_ini = _network_config.output_path.joinpath(network_ini.name)
        shutil.copyfile(network_ini, _output_ini)
        return NetworkConfigWrapper.from_data(network_ini, _network_config)

    @staticmethod
    def get_analysis_config_data(
        analysis_ini: Path, network_config: Optional[NetworkConfigWrapper]
    ) -> Optional[AnalysisConfigWrapper]:
        if not analysis_ini:
            return None
        _analysis_config = AnalysisConfigDataReader().read(analysis_ini)
        if isinstance(network_config, NetworkConfigWrapper):
            return ConfigFactory.get_analysis_config_with_network(
                analysis_ini, _analysis_config, network_config
            )
        else:
            return ConfigFactory.get_analysis_config_without_network(
                analysis_ini, _analysis_config
            )

    @staticmethod
    def get_analysis_config_with_network(
        analysis_ini: Path,
        config_data: AnalysisConfigData,
        network_config: NetworkConfigWrapper,
    ):
        return AnalysisConfigWrapper().from_data_with_network(
            analysis_ini, config_data, network_config
        )

    @staticmethod
    def get_analysis_config_without_network(
        analysis_ini: Path,
        config_data: AnalysisConfigData,
    ):
        _network_config = NetworkConfigWrapper()

        # Read existing files and graphs from static folder
        _static_dir = config_data.static_path
        if _static_dir and _static_dir.is_dir():
            _network_config.graph_files = NetworkConfigWrapper.read_graphs_from_config(
                _static_dir.joinpath("output_graph")
            )
        else:
            logging.error(f"Static dir not found. Value provided: {_static_dir}")

        # Read network config file to get network and origin_destination settings
        if config_data.output_path:
            _output_network_ini_file = config_data.output_path.joinpath("network.ini")
        else:
            _output_network_ini_file = Path()
        if _output_network_ini_file.is_file():
            _network_data = NetworkConfigDataReader().read(_output_network_ini_file)
            _network_config.config_data.network = _network_data.network
            _network_config.config_data.origins_destinations = (
                _network_data.origins_destinations
            )
            _network_config.config_data.hazard.aggregate_wl = (
                _network_data.hazard.aggregate_wl
            )
        else:
            logging.error(
                f"Network configuration not found. Value provided: {_output_network_ini_file}"
            )

        return AnalysisConfigWrapper().from_data_with_network(
            analysis_ini, config_data, _network_config
        )
