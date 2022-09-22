from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.config_reader_factory import ConfigReaderFactory


class ConfigWrapper:
    network_config: Optional[NetworkConfig] = None
    analysis_config: AnalysisConfigBase = None

    @classmethod
    def from_input_paths(
        cls, analysis_ini: Path, network_ini: Optional[Path]
    ) -> ConfigWrapper:
        """
        Initializes the `ConfigWrapper` object and reads both the network and analysis files into their respective configuration objects.

        Args:
            analysis_ini (Path): Path to the analysis *.ini file.
            network_ini (Optional[Path]): Path to the network *.ini file.

        Returns:
            ConfigWrapper: Instance with initialized `AnalysisConfigBase` and `NetworkConfig`.
        """
        _input_config = ConfigWrapper()
        _input_config.network_config = ConfigReaderFactory.get_reader(
            NetworkConfig
        ).read(network_ini)
        _input_config.analysis_config = ConfigReaderFactory.get_reader(
            AnalysisConfigBase
        ).read(analysis_ini, _input_config.network_config)
        return _input_config

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

        # We already validated the anlysis, just need to validate the network now.
        return self.network_config.is_valid()

    def configure(self) -> None:
        if self.network_config:
            self.network_config.configure()
        if self.analysis_config:
            self.analysis_config.configure()
