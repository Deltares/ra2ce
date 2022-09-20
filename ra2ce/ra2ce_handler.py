# -*- coding: utf-8 -*-
import logging
import sys
import warnings
from pathlib import Path
from typing import Optional

from ra2ce.ra2ce_input_config import Ra2ceInputConfig
from ra2ce.ra2ce_logging import Ra2ceLogger
from ra2ce.runners import AnalysisRunner, AnalysisRunnerFactory

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")


class Ra2ceHandler:
    _logger: logging.Logger = None

    def __init__(self, network: Optional[Path], analysis: Optional[Path]) -> None:
        _output_config = None
        self._logger = Ra2ceLogger(
            logging_dir=_output_config, logger_name="RA2CE"
        )._get_logger()
        self.input_config = Ra2ceInputConfig(network, analysis)

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
