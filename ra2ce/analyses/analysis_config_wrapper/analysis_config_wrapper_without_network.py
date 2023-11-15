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

from ra2ce.analyses.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_without_network import (
    AnalysisConfigDataValidatorWithoutNetwork,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper


class AnalysisConfigWrapperWithoutNetwork(AnalysisConfigWrapperBase):
    def __init__(self) -> None:
        self.config_data = AnalysisConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisConfigData
    ) -> AnalysisConfigWrapperWithoutNetwork:
        """
        Initializes an `AnalysisWithoutNetworkConfiguration` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (AnalysisIniConfigData): Ini data representation.

        Raises:
            FileNotFoundError: When the provided `ini file` cannot be found.

        Returns:
            AnalysisWithoutNetworkConfiguration: Initialized instance.
        """
        _new_analysis_config = cls()
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        _new_analysis_config.ini_file = ini_file
        _new_analysis_config.config_data = config_data
        _static_dir = config_data.static_path
        if _static_dir and _static_dir.is_dir():
            config_data.files = NetworkConfigWrapper._get_existent_network_files(
                _static_dir / "output_graph"
            )
        else:
            logging.error(f"Static dir not found. Value provided: {_static_dir}")
        _new_analysis_config.config_data.files = config_data.files
        return _new_analysis_config

    def configure(self) -> None:
        self.graphs = NetworkConfigWrapper.read_graphs_from_config(
            self.config_data.static_path.joinpath("output_graph")
        )
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        _validation_report = AnalysisConfigDataValidatorWithoutNetwork(
            self.config_data
        ).validate()
        return _file_is_valid and _validation_report.is_valid()
