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


from optparse import Option
from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis.analysis_ini_config_data import (
    AnalysisIniConfigData,
    AnalysisWithNetworkIniConfigData,
    AnalysisWithoutNetworkIniConfigData,
)
from ra2ce.configuration.analysis.analysis_with_network_config import (
    AnalysisWithNetworkConfiguration,
)
from ra2ce.configuration.analysis.analysis_without_network_config import (
    AnalysisWithoutNetworkConfiguration,
)
from ra2ce.configuration.network.network_config import NetworkConfig


class AnalysisConfigFactory:
    """
    Factory to help determine which AnalysisConfig should be created based on the input given.
    """

    @staticmethod
    def get_analysis_config(
        ini_file: Path,
        analysis_ini_config: AnalysisIniConfigData,
        network_config: Optional[NetworkConfig],
    ) -> AnalysisConfigBase:
        """
        Converts an `AnalysisIniConfigData` into the matching concrete class of `AnalysisConfigBase`.

        Args:
            ini_file (Path): Source `*.ini` file path to the FileObjectModel.
            analysis_ini_config (AnalysisIniConfigData): FileObjectModel to convert into DataObjectModel.
            network_config (Optional[NetworkConfig]): Complementary network configuration DataObjectModel to be used.

        Raises:
            NotImplementedError: When the `AnalysisIniConfigData` type has not been yet mapped to a DataObjectModel.

        Returns:
            AnalysisConfigBase: Concrete `AnalysisConfigBase` DataObjectModel for the given data.
        """
        if isinstance(analysis_ini_config, AnalysisWithNetworkIniConfigData):
            return AnalysisWithNetworkConfiguration.from_data_with_network(
                ini_file, analysis_ini_config, network_config
            )
        elif isinstance(analysis_ini_config, AnalysisWithoutNetworkIniConfigData):
            return AnalysisWithoutNetworkConfiguration.from_data(
                ini_file, analysis_ini_config
            )
        else:
            raise NotImplementedError(
                f"Analysis type {type(analysis_ini_config)} not currently supported."
            )
