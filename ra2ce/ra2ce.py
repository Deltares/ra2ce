# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

from pathlib import Path

# Local modules
from utils import parse_config, initiate_root_logger, configure_analyses
from checks import input_validation
from graph.networks import Network
from analyses.direct import analyses_direct
from analyses.indirect import analyses_indirect


def main():
    # Find the settings.ini file
    root_path = Path(__file__).resolve().parent.parent
    network_settings = root_path / "network.ini"
    analyses_settings = root_path / "settings.ini"

    # Read the configurations in network.ini and add the root path to the configuration dictionary.
    config_network = parse_config(path=network_settings)
    config_network['root_path'] = root_path

    # Read the configurations in analyses.ini and add the root path to the configuration dictionary.
    config_analyses = parse_config(path=analyses_settings)
    config_analyses['root_path'] = root_path

    # Initiate the log file, save in the output folder.
    initiate_root_logger(str(config_analyses['root_path'] / 'data' / config_analyses['project']['name'] / 'output' / 'RA2CE.log'))

    # Validate the configuration input.
    config_network = input_validation(config_network)
    config_analyses = input_validation(config_analyses)


    # Create a dictionary with direct and indirect analyses separately.
    config_analyses = configure_analyses(config_analyses)

    # Set the output paths in the configuration Dict for ease of saving to those folders.
    config_network['input'] = config_network['root_path'] / 'data' / config_network['project']['name'] / 'input'
    config_network['static'] = config_network['root_path'] / 'data' / config_network['project']['name'] / 'static'
    config_network['output'] = config_network['root_path'] / 'data' / config_network['project']['name'] / 'output'

    # Set the output paths in the configuration Dict for ease of saving to those folders.
    config_analyses['input'] = config_analyses['root_path'] / 'data' / config_analyses['project']['name'] / 'input'
    config_analyses['static'] = config_analyses['root_path'] / 'data' / config_analyses['project']['name'] / 'static'
    config_analyses['output'] = config_analyses['root_path'] / 'data' / config_analyses['project']['name'] / 'output'

    # Create the output folders
    if 'direct' in config_analyses:
        for a in config_analyses['direct']:
            output_path = config_analyses['output'] / a['analysis']
            output_path.mkdir(parents=True, exist_ok=True)

    if 'indirect' in config_analyses:
        for a in config_analyses['indirect']:
            output_path = config_analyses['output'] / a['analysis']
            output_path.mkdir(parents=True, exist_ok=True)

    # Create the network if not yet created
    network = Network(config_network)
    config_analyses = network.create(config_analyses)

    # Do the analyses
    if 'direct' in config_analyses:
        analyses_direct.DirectAnalyses(config_analyses).execute()

    if 'indirect' in config_analyses:
        analyses_indirect.IndirectAnalyses(config_analyses).execute()


if __name__ == '__main__':
    main()
