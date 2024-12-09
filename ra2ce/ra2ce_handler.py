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

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Optional

from shapely.errors import ShapelyDeprecationWarning

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.configuration.config_factory import ConfigFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from ra2ce.ra2ce_logger import Ra2ceLogger
from ra2ce.runners import AnalysisRunnerFactory

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.simplefilter(action="ignore", category=FutureWarning)


class Ra2ceHandler:
    """
    Top level class to handle the RA2CE analysis process.
    This class is used to orchestrate the analysis process based on the provided network and analysis configuration,
    including the logging configuration
    """

    input_config: ConfigWrapper

    def __init__(self, network: Optional[Path], analysis: Optional[Path]) -> None:
        if network or analysis:
            self._initialize_logger_from_files(network, analysis)
            self.input_config = ConfigFactory.get_config_wrapper(network, analysis)
        else:
            self._initialize_logger_from_config()

    @classmethod
    def from_config(
        cls, network: NetworkConfigData, analysis: AnalysisConfigData
    ) -> Ra2ceHandler:
        """
        Create a handler from the provided network and analysis configuration.

        Args:
            network (NetworkConfigData): Network configuration
            analysis (AnalysisConfigData): Analysis configuration

        Returns:
            Ra2ceHandler: The handler object
        """

        def set_config_paths(_analysis_config: AnalysisConfigWrapper) -> None:
            if not network:
                return
            _analysis_config.config_data.root_path = network.root_path
            _analysis_config.config_data.input_path = network.input_path
            _analysis_config.config_data.static_path = network.static_path
            _analysis_config.config_data.output_path = network.output_path

        def get_network_config() -> NetworkConfigWrapper | None:
            if not isinstance(network, NetworkConfigData):
                return None
            _network_config = NetworkConfigWrapper()
            _network_config.config_data = network
            if network.output_graph_dir:
                if network.output_graph_dir.is_dir():
                    _network_config.graph_files = (
                        _network_config.read_graphs_from_config(
                            network.output_graph_dir
                        )
                    )
                else:
                    network.output_graph_dir.mkdir(parents=True)
            return _network_config

        def get_analysis_config() -> AnalysisConfigWrapper | None:
            if not isinstance(analysis, AnalysisConfigData):
                return None
            _analysis_config = AnalysisConfigWrapper()
            _analysis_config.config_data = analysis
            set_config_paths(_analysis_config)
            if isinstance(_handler.input_config.network_config, NetworkConfigWrapper):
                _analysis_config.config_data.network = (
                    _handler.input_config.network_config.config_data.network
                )
                _analysis_config.config_data.origins_destinations = (
                    _handler.input_config.network_config.config_data.origins_destinations
                )
                _analysis_config.config_data.aggregate_wl = (
                    _handler.input_config.network_config.config_data.hazard.aggregate_wl
                )
                _analysis_config.graph_files = (
                    _handler.input_config.network_config.graph_files
                )
            return _analysis_config

        _handler = cls(None, None)
        _handler.input_config = ConfigWrapper()
        _handler.input_config.network_config = get_network_config()
        _handler.input_config.analysis_config = get_analysis_config()

        return _handler

    def _initialize_logger_from_files(
        self, network: Optional[Path], analysis: Optional[Path]
    ) -> None:
        _output_config = None
        if network:
            _output_config = NetworkConfigData.get_data_output(network)
        elif analysis:
            _output_config = AnalysisConfigData.get_data_output(analysis)
        else:
            logging.warning(
                "No valid location provided to start logging: no logger and logfile is created."
            )
            return
        Ra2ceLogger.initialize_file_logger(
            logging_dir=_output_config, logger_name="RA2CE"
        )

    def _initialize_logger_from_config(self) -> None:
        Ra2ceLogger.initialize_console_logger(logger_name="RA2CE")

    def configure(self) -> None:
        """
        Configures the `ConfigWrapper` with the current `AnalysisConfigData` and
        `NetworkConfigData` so that the analyses can be succesfully run.
        """
        self.input_config.configure()

    def run_analysis(self) -> list[AnalysisResultWrapper]:
        """
        Runs a Ra2ce analysis based on the provided network and analysis files.

        Args: None

        Raises:
            ValueError: If the input files are not valid

        Returns:
            list[AnalysisResultWrapper]: A list of analysis results
        """
        if not self.input_config.analysis_config:
            return
        if not self.input_config.is_valid_input():
            _error = "Error validating input files. Ra2ce will close now."
            logging.error(_error)
            raise ValueError(_error)

        return AnalysisRunnerFactory.run(self.input_config)

    @staticmethod
    def run_with_ini_files(
        network_ini_file: Path | None, analysis_ini_file: Path | None
    ) -> list[AnalysisResultWrapper]:
        """
        Streamlined method to directly run a `Ra2ce` analysis based
        on the provided `network` and `analysis` `.ini` files.

        This streamlined method allows for automatic initialization of the
        logger.

        Args:
            network_ini_file (Path | None): Location of the network file (`*.ini`).
            analysis_ini_file (Path | None): Location of the analysis file (`*.ini`).

        Returns:
            list[AnalysisResultWrapper]: A list of analyses results.
        """
        _handler = Ra2ceHandler(network_ini_file, analysis_ini_file)
        _handler.configure()
        return _handler.run_analysis()

    @staticmethod
    def run_with_config_data(
        network: NetworkConfigData | None, analysis: AnalysisConfigData | None
    ) -> list[AnalysisResultWrapper]:
        """
        Streamlined method to directly run a `Ra2ce` analysis based
        on the dataclasses for `Network` and `Analysis` instead of
        using `.ini` files.

        This streamlined method allows for automatic initialization of the
        logger.

        Args:
            network (NetworkConfigData | None):
                Dataclass containing all the information for the network.
            analysis (AnalysisConfigData | None):
                Dataclass containing all the information related to analyses.

        Returns:
            list[AnalysisResultWrapper]: A list of analyses results.
        """
        _handler = Ra2ceHandler.from_config(network, analysis)
        _handler.configure()
        return _handler.run_analysis()
