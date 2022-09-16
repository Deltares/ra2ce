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


from typing import Optional

from ra2ce.analyses.direct import analyses_direct
from ra2ce.analyses.indirect import analyses_indirect
from ra2ce.ra2ce_input import Ra2ceInput

# Local modules
from ra2ce.utils import initiate_root_logger


def analysis_handler(network_config: dict, analysis_config: dict, graphs: dict) -> None:
    """Directs the script to the right functions to run the analyses

    Args:
        network_config: Network configuration dict, from the network.ini input file
        analysis_config: Analysis configuration dict, from the analyses.ini input file
        graphs: Dictionary of a network (GDF) and graph(s) (NetworkX Graph)

    Returns:
        Nothing
    """
    # Do the analyses
    try:
        if "direct" in analysis_config:
            if network_config["hazard"]["hazard_map"] is not None:
                analyses_direct.DirectAnalyses(analysis_config, graphs).execute()
            else:
                logging.error(
                    "Please define a hazardmap in your network.ini file. Unable to calculate direct damages..."
                )

        if "indirect" in analysis_config:
            analyses_indirect.IndirectAnalyses(analysis_config, graphs).execute()

    except BaseException as e:
        logging.exception(
            f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
        )


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
        _network_config = self.input_config.network_config.config_data
        _analysis_config = self.input_config.analysis_config.config_data
        analysis_handler(
            _network_config, _analysis_config, self.input_config.network_config.graphs
        )
