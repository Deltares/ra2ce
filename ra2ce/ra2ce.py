# -*- coding: utf-8 -*-
"""
Main RA2CE script.
"""

import logging
import warnings
from pathlib import Path

warnings.filterwarnings(
    action="ignore", message=".*initial implementation of Parquet.*"
)
warnings.filterwarnings(action="ignore", message="All-NaN slice encountered")
warnings.filterwarnings(action="ignore", message="Value *not successfully written.*")


from typing import Optional, Tuple, Union  # Python object types

from .analyses.direct import analyses_direct
from .analyses.indirect import analyses_indirect
from .graph.hazard import Hazard
from .graph.networks import Network
from .io import read_graphs

# Local modules
from .utils import get_files, get_root_path, initiate_root_logger, load_config


def initialize_with_network_ini(
    root_path: Union[Path, str], network_ini: Union[Path, str]
) -> Tuple[dict, dict]:
    config_network = load_config(root_path, config_path=network_ini)
    initiate_root_logger(str(config_network["output"] / "RA2CE.log"))

    # Try to find pre-existing files
    files = get_files(config_network)
    return config_network, files


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


def get_output_folders(config: dict, analysis_type: str) -> None:
    # Create the output folders
    if analysis_type in config:
        for a in config[analysis_type]:
            output_path = config["output"] / a["analysis"]
            output_path.mkdir(parents=True, exist_ok=True)


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


def get_config_params(config_in: dict, config_out: dict, files: dict) -> dict:
    # The network_ini and analyses_ini are both called, copy the config values of the network ini
    # into the analyses config.
    config_out["files"] = files
    if config_in["network"] is not None:
        config_out["network"] = config_in["network"]
    if config_in["origins_destinations"] is not None:
        config_out["origins_destinations"] = config_in["origins_destinations"]
    return config_out


def get_network_config_params(root_path: Path, analysis_config: dict) -> dict:
    try:
        config_network = load_config(
            root_path,
            config_path=analysis_config["output"].joinpath("network.ini"),
            check=False,
        )
        analysis_config.update(config_network)
        analysis_config["origins_destinations"] = analysis_config["network"][
            "origins_destinations"
        ]
        return analysis_config
    except FileNotFoundError:
        logging.error(
            f"The configuration file 'network.ini' is not found at {analysis_config['output'].joinpath('network.ini')}."
            f"Please make sure to name your network settings file 'network.ini'."
        )
        quit()


def main(network_ini: str = None, analyses_ini: str = None) -> None:
    """Main function to start RA2CE. Runs RA2CE according to the settings in network_ini and analysis_ini.

    Reads the network and analyses ini files and chooses the right functions.

    Args:
        network_ini (string): Path to initialization file with the configuration for network creation.
        analyses_ini (string) : Path to initialization file with the configuration for the analyses.
    """

    # Find the network.ini and analysis.ini files
    root_path = get_root_path(network_ini, analyses_ini)

    if network_ini:
        # If no network_ini is provided, config and files are both None
        config_network, files = initialize_with_network_ini(root_path, network_ini)
        graphs = network_handler(config_network, files)
        graphs = hazard_handler(config_network, graphs, files)

    if analyses_ini:
        config_analyses = load_config(root_path, config_path=analyses_ini)

        if network_ini:
            # The logger is already made, just the analysis config needs to be updated with the network config parameters
            config_analyses = get_config_params(config_network, config_analyses, files)

        else:
            # Only the analyses.ini is called, initiate logger and load all network/graph files.
            initiate_root_logger(str(config_analyses["output"] / "RA2CE.log"))
            graphs = read_graphs(config_analyses)
            config_analyses = get_network_config_params(root_path, config_analyses)

        get_output_folders(config_analyses, "direct")
        get_output_folders(config_analyses, "indirect")

        analysis_handler(config_network, config_analyses, graphs)
