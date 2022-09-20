# -*- coding: utf-8 -*-
import logging
import sys
import warnings
from pathlib import Path
from typing import Optional

from ra2ce.configuration.analysis_ini_config_base import AnalysisConfigBase
from ra2ce.configuration.network_config import NetworkIniConfig
from ra2ce.ra2ce_input_config import Ra2ceInputConfig
from ra2ce.ra2ce_logging import Ra2ceLogger
from ra2ce.runners import AnalysisRunner, AnalysisRunnerFactory

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")


class Ra2ceHandler:
    def __init__(self, network: Optional[Path], analysis: Optional[Path]) -> None:
        self._initialize_logger(network, analysis)
        self.input_config = Ra2ceInputConfig(network, analysis)

    def _initialize_logger(
        self, network: Optional[Path], analysis: Optional[Path]
    ) -> None:
        _output_config = None
        if network:
            _output_config = NetworkIniConfig.get_data_output(network)
        elif analysis:
            _output_config = AnalysisConfigBaset_data_output(analysis)
        else:
            raise ValueError(
                "No valid location provided to start logging. Either network or analysis are required."
            )
        Ra2ceLogger(logging_dir=_output_config, logger_name="RA2CE")

    def configure(self) -> None:
        self.input_config.configure()

    def run_analysis(self) -> None:
        if not self.input_config.is_valid_input():
            logging.error("Error validating input files. Ra2ce will close now.")
            sys.exit()
        _runner: AnalysisRunner = AnalysisRunnerFactory.get_runner(self.input_config)
        try:
            _runner.run(self.input_config.analysis_config)
        except BaseException as e:
            logging.exception(
                f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
            )
