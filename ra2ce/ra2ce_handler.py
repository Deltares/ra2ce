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


from typing import Any, Dict, List, Optional

from ra2ce.analyses.direct import analyses_direct
from ra2ce.analyses.indirect import analyses_indirect
from ra2ce.graph.hazard import Hazard
from ra2ce.graph.networks import Network
from ra2ce.io import read_graphs

# Local modules
from ra2ce.utils import get_files, initiate_root_logger, load_config


def network_handler(config: dict, files: dict) -> Optional[dict]:
    try:
        network = Network(config, files)
        graphs = network.create()
        return graphs

    except BaseException as e:
        logging.exception(
            f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
        )


def hazard_handler(config: dict, graphs: dict, files: dict) -> Optional[dict]:
    if config["hazard"]["hazard_map"] is not None:
        # There is a hazard map or multiple hazard maps that should be intersected with the graph.
        hazard = Hazard(config, graphs, files)
        graphs = hazard.create()
        return graphs
    else:
        return None


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


from typing import Protocol


class IniConfiguration(Protocol):
    ini_file: Path
    root_dir: Path
    config_data: Dict = None
    graphs: List[Any] = None

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()


class NetworkIniConfiguration(IniConfiguration):
    files: List[Path] = None

    def __init__(self, ini_file: Path) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self.config_data = load_config(self.root_dir, config_path=self.ini_file)

    @property
    def root_dir(self) -> Path:
        return self.ini_file.parent.parent

    def configure(self) -> None:
        _output_graph = self.config_data["static"] / "output_graph"
        self.files = get_files(_output_graph)
        # Call Handlers (to rework)
        _graphs = network_handler(self.config_data, self.files)
        self.graphs = hazard_handler(self.config_data, _graphs, self.files)

    def is_valid(self) -> bool:
        return self.ini_file.is_file() and self.ini_file.suffix == ".ini"


class AnalysisIniConfigurationBase(IniConfiguration):
    ini_file: Path
    root_dir: Path
    config_data: Dict = None

    @property
    def root_dir(self) -> Path:
        return self.ini_file.parent.parent

    def initialize_output_dirs(self) -> None:
        """
        Initializes the required output directories for a Ra2ce analysis.
        """

        def _create_output_folders(analysis_type: str) -> None:
            # Create the output folders
            if not analysis_type in self.config_data.keys():
                return
            for a in self.config_data[analysis_type]:
                output_path = self.config_data["output"] / a["analysis"]
                output_path.mkdir(parents=True, exist_ok=True)

        _create_output_folders("direct")
        _create_output_folders("indirect")

    def is_valid(self) -> bool:
        return self.ini_file.is_file() and self.ini_file.suffix == ".ini"


class AnalysisWithNetworkConfiguration(AnalysisIniConfigurationBase):
    def __init__(self, ini_file: Path, network_config: NetworkIniConfiguration) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self._network_config = network_config
        self.config_data = load_config(self.root_dir, config_path=self.ini_file)

    def configure(self) -> None:
        self.config_data["files"] = self._network_config.files
        self.config_data["network"] = self._network_config.config_data.get(
            "network", None
        )
        self.config_data["origins_destinations"] = self._network_config.config_data.get(
            "origins_destinations", None
        )

        # When Network is present the graphs are retrieved from the already configured object.
        self.graphs = self._network_config.graphs
        self.initialize_output_dirs()


class AnalysisWithoutNetworkConfiguration(AnalysisIniConfigurationBase):
    def __init__(self, ini_file: Path) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self.config_data = load_config(self.root_dir, config_path=self.ini_file)

    def _update_with_network_configuration(self) -> dict:
        try:
            _output_network_ini_file = self.config_data["output"] / "network.ini"
            assert _output_network_ini_file.is_file()

            _config_network = load_config(
                self.root_dir,
                config_path=_output_network_ini_file,
                check=False,
            )
            self.config_data.update(_config_network)
            self.config_data["origins_destinations"] = self.config_data["network"][
                "origins_destinations"
            ]
        except FileNotFoundError:
            logging.error(
                f"The configuration file 'network.ini' is not found at {self.config_data['output'].joinpath('network.ini')}."
                f"Please make sure to name your network settings file 'network.ini'."
            )
            quit()

    def configure(self) -> None:
        self.graphs = read_graphs(self.config_data)
        self.config_data = self._update_with_network_configuration()
        self.initialize_output_dirs()


class Ra2ceInput:
    network_config: Optional[NetworkIniConfiguration] = None
    analysis_config: AnalysisIniConfigurationBase = None

    def __init__(self, network_ini: Optional[Path], analysis_ini: Path) -> None:
        if network_ini:
            self.network_config = NetworkIniConfiguration(network_ini)

        if analysis_ini:
            if self.network_config:
                self.analysis_config = AnalysisWithNetworkConfiguration(
                    analysis_ini, self.network_config
                )
            else:
                self.analysis_config = AnalysisWithoutNetworkConfiguration(analysis_ini)

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

        Returns:
            bool: Input parameters are valid for a ra2ce run.
        """
        # if not self.network_config.is_valid():
        #     logging.error(
        #         f"No valid network configuration provided. File provided: {self.network_config.ini_file}."
        #     )
        #     return False

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
        return True

    def configure(self) -> None:
        if self.network_config:
            self.network_config.configure()
        if self.analysis_config:
            self.analysis_config.configure()


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
