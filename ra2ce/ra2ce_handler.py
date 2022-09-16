# -*- coding: utf-8 -*-
import logging
import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")


from typing import Any, Optional, Protocol

from ra2ce.analyses.direct import analyses_direct
from ra2ce.analyses.indirect import analyses_indirect
from ra2ce.configuration.analysis_ini_configuration import AnalysisIniConfigurationBase
from ra2ce.ra2ce_input import Ra2ceInput

# Local modules
from ra2ce.utils import initiate_root_logger


class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: Ra2ceInput) -> bool:
        pass

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        pass


class DirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Direct Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: Ra2ceInput) -> bool:
        _network_config = ra2ce_input.network_config.config_data
        if not ("direct" in ra2ce_input.analysis_config.config_data):
            return False
        if not _network_config["hazard"]["hazard_map"]:
            logging.error(
                "Please define a hazardmap in your network.ini file. Unable to calculate direct damages."
            )
            return False
        return True

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        analyses_direct.DirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()


class IndirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Indirect Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: Ra2ceInput) -> bool:
        return super().can_run(ra2ce_input)

    def run(self, analysis_config: AnalysisIniConfigurationBase) -> None:
        analyses_indirect.IndirectAnalyses(
            analysis_config.config_data, analysis_config.graphs
        ).execute()


class AnalysisRunnerFactory:
    @staticmethod
    def get_runner(ra2ce_input: Ra2ceInput) -> AnalysisRunner:
        _available_runners = [DirectAnalysisRunner, IndirectAnalysisRunner]
        _supported_runners = [
            _runner for _runner in _available_runners if _runner.can_run(ra2ce_input)
        ]
        if not _supported_runners:
            logging.error("No analysis runner found for the given configuration.")

        if len(_supported_runners) > 1:
            logging.warn(
                f"More than one runner available, using {_supported_runners[0]}"
            )
        return _supported_runners[0]


class Ra2ceHandler:
    def __init__(self, network: Optional[Path], analysis: Optional[Path]) -> None:
        self.input_config = Ra2ceInput(network, analysis)
        self._initialize_logger(self.input_config)

    def _initialize_logger(self, input_config: Ra2ceInput) -> None:
        """
        Initializes the logger in the output directory, giving preference to the network output.

        Args:
            input_config (Ra2ceInput): Configuration containing ini data for both network and analysis.
        """
        _output_config = {}
        if input_config.network_config and input_config.network_config.is_valid():
            _output_config = input_config.network_config.config_data["output"]
        elif input_config.analysis_config.is_valid():
            _output_config = input_config.analysis_config.config_data["output"]
        else:
            raise ValueError()
        initiate_root_logger(_output_config / "RA2CE.log")

    def configure(self) -> None:
        self.input_config.configure()

    def run_analysis(self) -> None:
        if not self.input_config.is_valid_input():
            logging.error("Error validating input files. Ra2ce will close now.")
            sys.exit()
        _runner: AnalysisRunner = AnalysisRunnerFactory.get_runner(self.input_config)
        try:
            _runner().run(self.input_config.analysis_config)
        except BaseException as e:
            logging.exception(
                f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
            )
