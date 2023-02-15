from __future__ import annotations

import logging
from pathlib import Path

from ra2ce.configuration import AnalysisConfigBase, AnalysisIniConfigData, NetworkConfig


class AnalysisWithoutNetworkConfiguration(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = AnalysisIniConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisIniConfigData
    ) -> AnalysisWithoutNetworkConfiguration:
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
        _static_dir = config_data.get("static", None)
        if _static_dir and _static_dir.is_dir():
            config_data.files = NetworkConfig._get_existent_network_files(
                _static_dir / "output_graph"
            )
        else:
            logging.error(f"Static dir not found. Value provided: {_static_dir}")
        _new_analysis_config.config_data["files"] = config_data.files
        return _new_analysis_config

    def configure(self) -> None:
        self.graphs = NetworkConfig.read_graphs_from_config(
            self.config_data["static"] / "output_graph"
        )
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        return _file_is_valid and self.config_data.is_valid()
