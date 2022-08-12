# -*- coding: utf-8 -*-
"""
Main RA2CE script.
"""

from pathlib import Path
import click
import warnings
import logging

warnings.filterwarnings(action='ignore', message='.*initial implementation of Parquet.*')
warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
warnings.filterwarnings(action='ignore', message='Value *not successfully written.*')


# Local modules
from .utils import get_root_path, initiate_root_logger, load_config, get_files
from .graph.networks import Network, Hazard
from .analyses.direct import analyses_direct
from .analyses.indirect import analyses_indirect
from .io import read_graphs


def main(network_ini=None, analyses_ini=None):
    """Main function to start RA2CE. Runs RA2CE according to the settings in network_ini and analysis_ini.

    Reads the network and analyses ini files and chooses the right functions.

    Args:
        network_ini (string): Path to initialization file with the configuration for network creation.
        analyses_ini (string) : Path to initialization file with the configuration for the analyses.
    """
    # Find the network.ini and analysis.ini files
    root_path = get_root_path(network_ini, analyses_ini)

    if network_ini:
        config_network = load_config(root_path, config_path=network_ini)
        initiate_root_logger(str(config_network['output'] / 'RA2CE.log'))

        # Try to find pre-existing files
        files = get_files(config_network)

        network = Network(config_network, files)
        graphs = network.create()

        if config_network['hazard']['hazard_map'] is not None:
            # There is a hazard map or multiple hazard maps that should be intersected with the graph.
            # Overlay the hazard on the geodataframe as well (todo: combine with graph overlay if both need to be done?)
            hazard = Hazard(network, graphs, files)
            graphs = hazard.create()

    if analyses_ini:
        config_analyses = load_config(root_path, config_path=analyses_ini)

        if network_ini:
            # The network_ini and analyses_ini are both called, copy the config values of the network ini
            # into the analyses config.
            config_analyses['files'] = files
            if config_network['network'] is not None:
                config_analyses['network'] = config_network['network']
            if config_network['origins_destinations'] is not None:
                config_analyses['origins_destinations'] = config_network['origins_destinations']
        else:
            # Only the analyses.ini is called, initiate logger and load all network/graph files.
            initiate_root_logger(str(config_analyses['output'] / 'RA2CE.log'))
            graphs = read_graphs(config_analyses)
            try:
                config_network = load_config(root_path, config_path=config_analyses['output'].joinpath('network.ini'),
                                             check=False)
                config_analyses.update(config_network)
                config_analyses['origins_destinations'] = config_analyses['network']['origins_destinations']
            except FileNotFoundError:
                logging.error(f"The configuration file 'network.ini' is not found at {config_analyses['output'].joinpath('network.ini')}."
                              f"Please make sure to name your network settings file 'network.ini'.")
                quit()

        # Create the output folders
        if 'direct' in config_analyses:
            for a in config_analyses['direct']:
                output_path = config_analyses['output'] / a['analysis']
                output_path.mkdir(parents=True, exist_ok=True)

        if 'indirect' in config_analyses:
            for a in config_analyses['indirect']:
                output_path = config_analyses['output'] / a['analysis']
                output_path.mkdir(parents=True, exist_ok=True)

        # Do the analyses
        if 'direct' in config_analyses:
            if config_network['hazard']['hazard_map'] is not None:
                analyses_direct.DirectAnalyses(config_analyses, graphs).execute()
            else:
                logging.error('Please define a hazardmap in your network.ini file. Unable to calculate direct damages...')

        if 'indirect' in config_analyses:
            analyses_indirect.IndirectAnalyses(config_analyses, graphs).execute()
