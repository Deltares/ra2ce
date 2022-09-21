from pathlib import Path

from ra2ce.configuration.network.network_config import NetworkConfig
from ra2ce.configuration.network.network_ini_config_data import NetworkIniConfigData
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class NetworkIniConfigurationReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> NetworkConfig:
        if not ini_file:
            return None
        _config_data = self._import_configuration(ini_file)
        self._update_path_values(_config_data)
        self._copy_output_files(ini_file, _config_data)
        _network_config_data = NetworkIniConfigData.from_dict(_config_data)
        return NetworkConfig(ini_file, _network_config_data)

    def _import_configuration(self, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        _root_path = NetworkConfig.get_network_root_dir(config_path)
        if not config_path.is_file():
            config_path = _root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parent.name
        _config["root_path"] = _root_path

        _hazard = _config.get("hazard", None)
        if _hazard and "hazard_field_name" in _hazard:
            if _hazard["hazard_field_name"]:
                _hazard["hazard_field_name"] = _hazard["hazard_field_name"].split(",")

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        _config["input"] = config_path.parent / "input"
        _config["static"] = config_path.parent / "static"
        return _config
