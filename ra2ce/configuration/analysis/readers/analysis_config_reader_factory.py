from pathlib import Path
from typing import Optional

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.analysis.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.analysis.readers.analysis_with_network_config_reader import (
    AnalysisWithNetworkConfigReader,
)
from ra2ce.configuration.analysis.readers.analysis_without_network_config_reader import (
    AnalysisWithoutNetworkConfigReader,
)


class AnalysisConfigReaderFactory:
    @staticmethod
    def get_reader(
        network_config: Optional[NetworkConfig],
    ) -> AnalysisConfigReaderBase:
        if network_config:
            return AnalysisWithNetworkConfigReader(network_config)
        return AnalysisWithoutNetworkConfigReader()

    def read(
        self, ini_file: Path, network_config: Optional[NetworkConfig]
    ) -> AnalysisConfigBase:
        _reader = self.get_reader(network_config)
        return _reader.read(ini_file)
