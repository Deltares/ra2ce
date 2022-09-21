from pathlib import Path

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis_without_network_config import (
    AnalysisWithoutNetworkConfiguration,
)
from ra2ce.configuration.ini_config_protocol import AnalysisIniConfigData
from ra2ce.configuration.network_config import NetworkConfig
from ra2ce.configuration.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class NetworkInAnalysisIniConfigReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> NetworkConfig:
        if not ini_file:
            return None
        _config_data = self._import_configuration(ini_file)
        return NetworkConfig(ini_file, _config_data)

    def _import_configuration(self, config_path: Path) -> dict:
        _root_path = AnalysisConfigBase.get_network_root_dir(config_path)
        if not config_path.is_file():
            config_path = _root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parent.name
        _config["root_path"] = _root_path

        return _config


class AnalysisWithoutNetworkConfigReader(AnalysisConfigReaderBase):
    def read(self, ini_file: Path) -> AnalysisWithoutNetworkConfiguration:
        if not ini_file:
            return None
        _analisis_config = self._get_analysis_config_data(ini_file)
        _output_network_ini_file = _analisis_config["output"] / "network.ini"
        _network_config = NetworkInAnalysisIniConfigReader().read(
            _output_network_ini_file
        )
        _analisis_config.update(_network_config)
        _analisis_config["origins_destinations"] = _analisis_config["network"][
            "origins_destinations"
        ]
        _analysis_config_data = AnalysisIniConfigData.from_dict(_analisis_config)

        return AnalysisWithoutNetworkConfiguration(ini_file, _analysis_config_data)

    def _get_analysis_config_data(self, ini_file: Path) -> dict:
        _root_path = AnalysisConfigBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        _config_data = self._convert_analysis_types(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return _config_data
