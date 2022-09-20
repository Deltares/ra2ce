from pathlib import Path

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis_with_network_config import (
    AnalysisWithNetworkConfiguration,
)
from ra2ce.configuration.network_config import NetworkIniConfig
from ra2ce.configuration.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)


class AnalysisWithNetworkConfigReader(AnalysisConfigReaderBase):
    def __init__(self, network_data: NetworkIniConfig) -> None:
        self._network_data = network_data
        if not network_data:
            raise ValueError(
                "Network data mandatory for an AnalysisIniConfigurationReader reader."
            )

    def read(self, ini_file: Path) -> AnalysisWithNetworkConfiguration:
        if not ini_file:
            return None
        _root_path = AnalysisConfigBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        _config_data = self._convert_analysis_types(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return AnalysisWithNetworkConfiguration(
            ini_file, _config_data, self._network_data
        )
