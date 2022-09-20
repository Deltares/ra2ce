from pathlib import Path

from ra2ce.configuration.network_ini_configuration import NetworkIniConfiguration
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.io.readers.ini_file_reader import IniFileReader


class NetworkIniConfigurationReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> NetworkIniConfiguration:
        if not ini_file:
            return None
        _root_dir = NetworkIniConfiguration.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_dir, ini_file)
        self._update_path_values(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return NetworkIniConfiguration(ini_file, _config_data)

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parts[-2]
        _config["root_path"] = root_path

        if "hazard" in _config:
            if "hazard_field_name" in _config["hazard"]:
                if _config["hazard"]["hazard_field_name"]:
                    _config["hazard"]["hazard_field_name"] = _config["hazard"][
                        "hazard_field_name"
                    ].split(",")

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        _config["input"] = _config["root_path"] / _config["project"]["name"] / "input"
        _config["static"] = _config["root_path"] / _config["project"]["name"] / "static"
        # config["output"] = config["root_path"] / config["project"]["name"] / "output"
        return _config
