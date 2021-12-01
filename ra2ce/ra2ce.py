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

warnings.filterwarnings('ignore', message='.*initial implementation of Parquet.*')

# Local modules
from .utils import initiate_root_logger, load_config
from .graph.networks import Network, Hazard
from .analyses.direct import analyses_direct
from .analyses.indirect import analyses_indirect


def main(network_ini=None, analyses_ini=None):
    # Find the network.ini and analysis.ini files
    root_path = Path(__file__).resolve().parent.parent

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

        if 'indirect' in config_analyses:
            analyses_indirect.IndirectAnalyses(config_analyses, graphs).execute()

        if 'direct' in config_analyses:
            if config_network['hazard']['hazard_map'] is not None:
                analyses_direct.DirectAnalyses(config_analyses, graphs).execute()
            else:
                logging.error('Please define a hazardmap in your network.ini file. Unable to calculate direct damages...')



@click.command()
@click.option("--network_ini", default=None, help="Full path to the network.ini file.")
@click.option("--analyses_ini", default=None, help="Full path to the analyses.ini file.")
def cli(network_ini, analyses_ini):
    main(network_ini, analyses_ini)


if __name__ == '__main__':
    # cli()
    #rootpath = r'c:\Python\ra2ce\data\test_pbf'
    rootpath = r'c:\Python\ra2ce\data\KBN2'
    #rootpath = r'c:\Python\ra2ce\data\1_test_network_shape'
    main(rootpath + r"\network.ini", rootpath + r"\analyses1.ini")
