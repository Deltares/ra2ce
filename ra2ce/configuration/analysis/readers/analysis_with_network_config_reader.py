from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis.analysis_ini_config_data import (
    AnalysisWithNetworkIniConfigData,
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

    def read(self, ini_file: Path) -> Optional[AnalysisWithNetworkIniConfigData]:
        if not ini_file:
            return None
        _root_path = AnalysisConfigBase.get_network_root_dir(ini_file)
        _config_data = self._import_configuration(_root_path, ini_file)
        _config_data = self._convert_analysis_types(_config_data)
        self._copy_output_files(ini_file, _config_data)
        return AnalysisWithNetworkIniConfigData.from_dict(_config_data)
