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


# -*- coding: utf-8 -*-
import logging
import warnings
from pathlib import Path
from typing import Optional

from shapely.errors import ShapelyDeprecationWarning

from ra2ce.analyses.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analyses.analysis_config_wrapper import (
    AnalysisConfigWrapper,
)
from ra2ce.configuration.config_factory import ConfigFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper
from ra2ce.ra2ce_logging import Ra2ceLogger
from ra2ce.runners import AnalysisRunnerFactory

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.simplefilter(action="ignore", category=FutureWarning)


class Ra2ceHandler:
    input_config: Optional[ConfigWrapper] = None

    def __init__(self, network: Optional[Path], analysis: Optional[Path]) -> None:
        self._initialize_logger(network, analysis)
        self.input_config = ConfigFactory.get_config_wrapper(network, analysis)

    def _initialize_logger(
        self, network: Optional[Path], analysis: Optional[Path]
    ) -> None:
        _output_config = None
        if network:
            _output_config = NetworkConfigData.get_data_output(network)
        elif analysis:
            _output_config = AnalysisConfigData.get_data_output(analysis)
        else:
            raise ValueError(
                "No valid location provided to start logging. Either network or analysis are required."
            )
        Ra2ceLogger(logging_dir=_output_config, logger_name="RA2CE")

    def configure(self) -> None:
        self.input_config.configure()

    def run_analysis(self) -> None:
        """
        Runs a Ra2ce analysis based on the provided network and analysis files.
        """
        if not self.input_config.is_valid_input():
            _error = "Error validating input files. Ra2ce will close now."
            logging.error(_error)
            raise ValueError(_error)

        _runner = AnalysisRunnerFactory.get_runner(self.input_config)
        _runner.run(self.input_config.analysis_config)
