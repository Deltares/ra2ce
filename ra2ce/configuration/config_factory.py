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


from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis.analysis_config_factory import AnalysisConfigFactory
from ra2ce.configuration.analysis.readers.analysis_config_reader_factory import (
    AnalysisConfigReaderFactory,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.configuration.network.network_config import NetworkConfig
from ra2ce.configuration.network.readers.network_ini_config_reader import (
    NetworkIniConfigDataReader,
)


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
    def get_network_config_data(network_ini: Path) -> Optional[NetworkConfig]:
        if not network_ini:
            return None
        _ini_config_data = NetworkIniConfigDataReader().read(network_ini)
        return NetworkConfig.from_data(network_ini, _ini_config_data)

    @staticmethod
    def get_analysis_config_data(
        analysis_ini: Path, network_config: Optional[NetworkConfig]
    ) -> Optional[AnalysisConfigBase]:
        if not analysis_ini:
            return None
        _ini_config_data = AnalysisConfigReaderFactory().read(
            analysis_ini, network_config
        )
        return AnalysisConfigFactory.get_analysis_config(
            analysis_ini, _ini_config_data, network_config
        )
