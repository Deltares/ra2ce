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
from configparser import ConfigParser
from pathlib import Path

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigDataWithoutNetwork,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.graph.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)


class AnalysisConfigReaderWithoutNetwork(AnalysisConfigReaderBase):
    _parser: ConfigParser

    def read(self, ini_file: Path) -> AnalysisConfigDataWithoutNetwork:
        """
        Read the configuration from analysis.ini and append with data from network.ini.
        The file network.ini should be in the output folder.

        Args:
            ini_file (Path): Path of analysis.ini

        Returns:
            AnalysisConfigDataWithoutNetwork
        """
        _config = super().read(ini_file)
        _config_data = AnalysisConfigDataWithoutNetwork(**_config.__dict__)

        self._copy_output_files(ini_file, _config_data)

        _output_network_ini_file = _config_data.output_path.joinpath("network.ini")
        _network_config = NetworkConfigDataReader().read(_output_network_ini_file)
        _config_data.update(_network_config.to_dict())
        _network = _config_data.network
        if _network:
            _config_data.origins_destinations = _network.origins_destinations
        else:
            logging.warn(f"Not found network key for the Analysis {ini_file}")

        return _config_data
