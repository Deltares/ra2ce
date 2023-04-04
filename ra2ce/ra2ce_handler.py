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
import sys
import warnings
from pathlib import Path
from typing import Optional

from shapely.errors import ShapelyDeprecationWarning

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.config_factory import ConfigFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.ra2ce_logging import Ra2ceLogger
from ra2ce.runners import AnalysisRunner, AnalysisRunnerFactory

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
            _output_config = NetworkConfig.get_data_output(network)
        elif analysis:
            _output_config = AnalysisConfigBase.get_data_output(analysis)
        else:
            raise ValueError(
                "No valid location provided to start logging. Either network or analysis are required."
            )
        Ra2ceLogger(logging_dir=_output_config, logger_name="RA2CE")

    def configure(self) -> None:
        self.input_config.configure()

    def run_analysis(self) -> None:
        if not self.input_config.is_valid_input():
            logging.error("Error validating input files. Ra2ce will close now.")
            sys.exit()
        _runner: AnalysisRunner = AnalysisRunnerFactory.get_runner(self.input_config)
        try:
            _runner.run(self.input_config.analysis_config)
        except BaseException as e:
            logging.exception(
                f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
            )
