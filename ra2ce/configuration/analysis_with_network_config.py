from pathlib import Path

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.network_config import NetworkIniConfig
from ra2ce.configuration.validators import AnalysisIniConfigValidator


class AnalysisWithNetworkConfiguration(AnalysisConfigBase):
    def __init__(
        self,
        ini_file: Path,
        analysis_data: dict,
        network_config: NetworkIniConfig,
    ) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self._network_config = network_config
        self.config_data = analysis_data

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
        return (
            _file_is_valid and AnalysisIniConfigValidator(self.config_data).validate()
        )
