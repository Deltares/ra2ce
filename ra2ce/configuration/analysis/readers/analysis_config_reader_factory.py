"""
GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Deltares

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

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.analysis.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.analysis.readers.analysis_with_network_config_reader import (
    AnalysisWithNetworkConfigReader,
)
from ra2ce.configuration.analysis.readers.analysis_without_network_config_reader import (
    AnalysisWithoutNetworkConfigReader,
)


class AnalysisConfigReaderFactory:
    @staticmethod
    def get_reader(
        network_config: Optional[NetworkConfig],
    ) -> AnalysisConfigReaderBase:
        if network_config:
            return AnalysisWithNetworkConfigReader(network_config)
        return AnalysisWithoutNetworkConfigReader()

    def read(
        self, ini_file: Path, network_config: Optional[NetworkConfig]
    ) -> AnalysisConfigBase:
        _reader = self.get_reader(network_config)
        return _reader.read(ini_file)
