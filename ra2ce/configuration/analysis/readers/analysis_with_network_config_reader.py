from pathlib import Path

from ra2ce.configuration.analysis import AnalysisConfigBase, AnalysisIniConfigData
from ra2ce.configuration.analysis.analysis_with_network_config import (
    AnalysisWithNetworkConfiguration,
)
from ra2ce.configuration.analysis.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.network import NetworkConfig


class AnalysisWithNetworkConfigReader(AnalysisConfigReaderBase):
    def __init__(self, network_data: NetworkConfig) -> None:
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
        _analysis_config_data = AnalysisIniConfigData.from_dict(_config_data)
        return AnalysisWithNetworkConfiguration.from_data_with_network(
            ini_file, _analysis_config_data, self._network_data
        )
