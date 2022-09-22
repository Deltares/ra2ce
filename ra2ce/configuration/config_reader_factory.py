from pathlib import Path
from typing import Type

from ra2ce.configuration.analysis.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.analysis.readers.analysis_config_reader_factory import (
    AnalysisConfigReaderFactory,
)
from ra2ce.configuration.config_protocol import ConfigProtocol
from ra2ce.configuration.network.network_config import NetworkConfig
from ra2ce.configuration.network.readers.network_ini_config_reader import (
    NetworkIniConfigDataReader,
)
from ra2ce.io.readers.file_reader_protocol import FileReaderProtocol


class ConfigReaderFactory:
    @staticmethod
    def get_reader(config_type: Type[ConfigProtocol]) -> FileReaderProtocol:
        raise NotImplementedError(f"WORK IN PROGRESS.")
        if config_type == NetworkConfig:
            return NetworkIniConfigDataReader()
        elif config_type == AnalysisConfigBase:
            return AnalysisConfigReaderFactory()
        else:
            raise NotImplementedError(
                f"This factory does not support config type {config_type}"
            )
