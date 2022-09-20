from pathlib import Path

from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.configuration.network_ini_configuration import NetworkIniConfiguration


class NetworkIniConfigurationReader(IniConfigurationReaderBase):
    def read(self, ini_file: Path) -> NetworkIniConfiguration:
        if not ini_file:
            return None
        _root_dir = NetworkIniConfiguration.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_dir, ini_file)
        # self._update_path_values(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return NetworkIniConfiguration(ini_file, _config_data)
