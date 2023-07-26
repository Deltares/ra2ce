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

from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_with_network_config_reader import (
    AnalysisConfigReaderWithNetwork,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_without_network_config_reader import (
    AnalysisConfigReaderWithoutNetwork,
)
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData


class AnalysisConfigReaderFactory:
    @staticmethod
    def get_reader(
        network_config: Optional[NetworkConfigData],
    ) -> AnalysisConfigReaderBase:
        if network_config:
            return AnalysisConfigReaderWithNetwork(network_config)
        return AnalysisConfigReaderWithoutNetwork()

    def read(
        self, ini_file: Path, network_config: Optional[NetworkConfigData]
    ) -> AnalysisConfigWrapperBase:
        _reader = self.get_reader(network_config)
        return _reader.read(ini_file)
