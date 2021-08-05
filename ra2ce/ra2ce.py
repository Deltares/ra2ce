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
from shutil import copyfile

def main():
    # Find the settings.ini file
    root_path = Path(__file__).resolve().parent.parent


    def load_config(root_path, type):
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        settings = root_path / "{}.ini".format(type)
        config = parse_config(root_path, path=settings)
        config['root_path'] = root_path

        # Validate the configuration input.
        config = input_validation(config)

        if type == 'analyses':
            # Create a dictionary with direct and indirect analyses separately.
            config = configure_analyses(config)

        # Set the output paths in the configuration Dict for ease of saving to those folders.
        config['input'] = config['root_path'] / 'data' / config['project']['name'] / 'input'
        config['static'] = config['root_path'] / 'data' / config['project']['name'] / 'static'
        config['output'] = config['root_path'] / 'data' / config['project']['name'] / 'output'
        copyfile(settings, config['output'] / '{}.ini'.format(type))
        return config

    config_network = load_config(root_path, type='network')
    config_analyses = load_config(root_path, type='analyses')

    # Initiate the log file, save in the output folder.
    initiate_root_logger(str(config_network['output'] / 'RA2CE.log'))

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
