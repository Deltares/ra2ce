# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

from pathlib import Path

# Local modules
from utils import parse_config, initiate_root_logger, configure_analyses, load_config
from graph.networks import Network
from analyses.direct import analyses_direct
from analyses.indirect import analyses_indirect


def main(network_ini, analyses_ini):
    # Find the network.ini and analysis.ini files
    root_path = Path(__file__).resolve().parent.parent

    config_network = load_config(root_path, config_path=network_ini)
    config_analyses = load_config(root_path, config_path=analyses_ini)

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
    main(r"D:\ra2ceMaster\ra2ce\data\test\network.ini", r"D:\ra2ceMaster\ra2ce\data\test\analyses.ini")
