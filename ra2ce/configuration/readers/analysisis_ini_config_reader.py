from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis_ini_configuration import (
    AnalysisIniConfigurationBase,
    AnalysisWithNetworkConfiguration,
    AnalysisWithoutNetworkConfiguration,
)
from ra2ce.configuration.network_ini_configuration import NetworkIniConfiguration
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.configuration.validators.ini_config_validator_base import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class AnalysisIniConfigurationReader(IniConfigurationReaderBase):
    def __init__(self, network_data: Optional[NetworkIniConfiguration]) -> None:
        self._network_data = network_data

    def _convert_analysis_types(self, config: dict) -> dict:
        def set_analysis_values(config_type: str):
            if config_type in config:
                (config[config_type]).append(config[a])
            else:
                config[config_type] = [config[a]]

        analyses_names = [a for a in config.keys() if "analysis" in a]
        for a in analyses_names:
            if any(t in config[a]["analysis"] for t in DirectAnalysisNameList):
                set_analysis_values("direct")
            elif any(t in config[a]["analysis"] for t in IndirectAnalysisNameList):
                set_analysis_values("indirect")
            del config[a]

        return config

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parts[-2]
        _config["root_path"] = root_path

        # TODO: This might only be relevant for NETWORK reader.
        # REMOVE: if only relevant for NetworkConfigReader
        _hazard = _config.get("hazard", None)
        if _hazard and "hazard_field_name" in _hazard:
            if _hazard["hazard_field_name"]:
                _hazard["hazard_field_name"] = _hazard["hazard_field_name"].split(",")

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        _config["input"] = _config["root_path"] / _config["project"]["name"] / "input"
        _config["static"] = _config["root_path"] / _config["project"]["name"] / "static"
        # config["output"] = config["root_path"] / config["project"]["name"] / "output"
        return _config

    def read(self, ini_file: Path) -> AnalysisIniConfigurationBase:
        if not ini_file:
            return None
        _root_path = AnalysisIniConfigurationBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        # self._update_path_values(_config_data)
        _config_data = self._convert_analysis_types(_config_data)
        self._copy_output_files(ini_file, _config_data)
        if self._network_data:
            return AnalysisWithNetworkConfiguration(
                ini_file, _config_data, self._network_data
            )
        else:
            return AnalysisWithoutNetworkConfiguration(ini_file, _config_data)
