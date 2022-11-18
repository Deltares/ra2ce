from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ra2ce.configuration import AnalysisConfigBase, NetworkConfig


class ConfigWrapper:
    network_config: Optional[NetworkConfig] = None
    analysis_config: AnalysisConfigBase = None

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

        if self.network_config and not self.network_config.is_valid():
            logging.error("No valid network.ini file provided. Program will close.")
            return False

        if self.network_config and (_root_analysis != self.network_config.root_dir):
            logging.error(
                "Root directory differs between network and analyses .ini files"
            )
            return False

        return True

    def configure(self) -> None:
        if self.network_config:
            self.network_config.configure()
        if self.analysis_config:
            self.analysis_config.configure()
