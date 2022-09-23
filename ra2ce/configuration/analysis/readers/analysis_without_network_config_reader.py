import logging
from pathlib import Path
from typing import Optional

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.analysis.analysis_ini_config_data import (
    AnalysisWithoutNetworkIniConfigData,
)
from ra2ce.configuration.analysis.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class NetworkInAnalysisIniConfigReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> Optional[NetworkConfig]:
        if not ini_file:
            return None
        _config_data = self._import_configuration(ini_file)
        return NetworkConfig.from_data(ini_file, _config_data)

    def _import_configuration(self, config_path: Path) -> dict:
        _root_path = AnalysisConfigBase.get_network_root_dir(config_path)
        if not config_path.is_file():
            config_path = _root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parent.name
        _config["root_path"] = _root_path

        return _config


class AnalysisWithoutNetworkConfigReader(AnalysisConfigReaderBase):
    def read(self, ini_file: Path) -> Optional[AnalysisWithoutNetworkIniConfigData]:
        if not ini_file:
            return None
        _analisis_config_dict = self._get_analysis_config_data(ini_file)
        _output_network_ini_file = _analisis_config_dict["output"] / "network.ini"
        _network_config: NetworkConfig = NetworkInAnalysisIniConfigReader().read(
            _output_network_ini_file
        )
        _analisis_config_dict.update(_network_config.config_data)
        _network = _analisis_config_dict.get("network", None)
        if _network:
            _analisis_config_dict["origins_destinations"] = _network.get(
                "origins_destinations", None
            )
        else:
            logging.warn(f"Not found network key for the Analysis {ini_file}")
        return AnalysisWithoutNetworkIniConfigData.from_dict(_analisis_config_dict)

    def _get_analysis_config_data(self, ini_file: Path) -> dict:
        _root_path = AnalysisConfigBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        _config_data = self._convert_analysis_types(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return _config_data
