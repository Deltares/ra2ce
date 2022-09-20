import logging
from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.network_config import NetworkIniConfig
from ra2ce.configuration.readers import (
    AnalysisConfigReaderFactory,
    NetworkIniConfigurationReader,
)


class Ra2ceInputConfig:
    network_config: Optional[NetworkIniConfig] = None
    analysis_config: AnalysisConfigBase = None

    def __init__(self, network_ini: Optional[Path], analysis_ini: Path) -> None:
        self.network_config = NetworkIniConfigurationReader().read(network_ini)
        self.analysis_config = AnalysisConfigReaderFactory().read(
            analysis_ini, self.network_config
        )

    def get_root_dir(self) -> Path:
        if self.network_config.ini_file:
            return self.network_config.root_dir
        elif self.analysis_config.ini_file:
            return self.analysis_config.root_dir
        else:
            raise ValueError()

    def is_valid_input(self) -> bool:
        """
        Validates whether the input is valid. This require that at least the analysis ini file is given.
        TODO: Very unclear what a valid input is, needs to be better specified.

        Returns:
            bool: Input parameters are valid for a ra2ce run.
        """
        if not self.analysis_config or not self.analysis_config.is_valid():
            logging.error("No valid analyses.ini file provided. Program will close.")
            return False

        _root_analysis = self.analysis_config.root_dir
        if not _root_analysis.is_dir():
            logging.error(f"Path {_root_analysis} does not exist.")
            return False

        if self.network_config and (_root_analysis != self.network_config.root_dir):
            logging.error(
                "Root directory differs between network and analyses .ini files"
            )
            return False

        return self.network_config.is_valid() and self.analysis_config.is_valid()

    def configure(self) -> None:
        if self.network_config:
            self.network_config.configure()
        if self.analysis_config:
            self.analysis_config.configure()
