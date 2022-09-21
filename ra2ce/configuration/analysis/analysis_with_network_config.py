from __future__ import annotations

from pathlib import Path

from ra2ce.configuration import AnalysisConfigBase, AnalysisIniConfigData, NetworkConfig


class AnalysisWithNetworkConfiguration(AnalysisConfigBase):

    def __init__(self) -> None:
        self.config_data = AnalysisIniConfigData()

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: AnalysisIniConfigData
    ) -> AnalysisWithNetworkConfiguration:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        _new_analysis = cls()
        _new_analysis.ini_file = ini_file
        _new_analysis.config_data = config_data

    @classmethod
    def from_data_with_network(
        cls, ini_file: Path, config_data: AnalysisIniConfigData, network_config: NetworkConfig
    ) -> AnalysisWithNetworkConfiguration:
        _new_analysis = cls.from_data(ini_file, config_data)
        _new_analysis._network_config = network_config
        return _new_analysis

    def configure(self) -> None:
        self.config_data["files"] = self._network_config.files
        self.config_data["network"] = self._network_config.config_data.get(
            "network", None
        )
        self.config_data["origins_destinations"] = self._network_config.config_data.get(
            "origins_destinations", None
        )

        # When Network is present the graphs are retrieved from the already configured object.
        self.graphs = self._network_config.graphs
        self.initialize_output_dirs()

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        return _file_is_valid and self.config_data.is_valid()
