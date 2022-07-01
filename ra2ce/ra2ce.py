# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
@author: M. Kwant, Deltares
"""

from pathlib import Path
import click
import warnings
import logging

warnings.filterwarnings(action='ignore', message='.*initial implementation of Parquet.*')
warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
warnings.filterwarnings(action='ignore', message='Value *not successfully written.*')


# Local modules
from .utils import get_root_path, initiate_root_logger, load_config
from .graph.networks import Network, Hazard
from .analyses.direct import analyses_direct
from .analyses.indirect import analyses_indirect


def main(network_ini=None, analyses_ini=None):
    """Main function to start RA2CE. Runs the RA2CE tool according to the settings made in network_ini and analysis_ini.

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

        network = Network(config_network)
        graphs = network.create()

        if config_network['hazard']['hazard_map'] is not None:
            # There is a hazard map or multiple hazard maps that should be intersected with the graph.
            # Overlay the hazard on the geodataframe as well (todo: combine with graph overlay if both need to be done?)
            hazard = Hazard(network, graphs)
            graphs = hazard.create()

    if analyses_ini:
        config_analyses = load_config(root_path, config_path=analyses_ini)
        if network_ini:
            config_analyses['files'] = network.config['files']
        else:
            initiate_root_logger(str(config_analyses['output'] / 'RA2CE.log'))

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
        if network_ini:
            if config_network['network'] is not None:
                config_analyses['network'] = config_network['network']
            if config_network['origins_destinations'] is not None:
                config_analyses['origins_destinations'] = config_network['origins_destinations']
            if config_network['hazard']['hazard_map'] is not None:
                config_analyses['hazard_names'] = [haz.stem for haz in config_network['hazard']['hazard_map']]

        if 'direct' in config_analyses:
            if config_network['hazard']['hazard_map'] is not None:
                analyses_direct.DirectAnalyses(config_analyses, graphs).execute()
            else:
                logging.error('Please define a hazardmap in your network.ini file. Unable to calculate direct damages...')

        if 'indirect' in config_analyses:
            analyses_indirect.IndirectAnalyses(config_analyses, graphs).execute()
