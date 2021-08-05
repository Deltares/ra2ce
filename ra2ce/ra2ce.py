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
    # Find the settings.ini file,c:\Python\RACE\ra2ce\data\test_shp\
    root_path = Path(__file__).resolve().parent.parent
    #network_settings = root_path / "network.ini"
    network_settings = root_path / 'data' / 'test_shp' / "settings.ini"
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
    #config_network = input_validation(config_network)
    #config_analyses = input_validation(config_analyses)


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

    # def get_existing_networks(self):
    #
    #     # if any('multi_link_origin_destination' in a['analysis'] for a in self.config['indirect']):
    #     #     # Check which analyses require origin and destination nodes to be added to the graph and which ones already have been created.
    #     #     use_existing_od = [a for a in self.config['indirect'] if (a['analysis'] in ['optimal_route_origin_destination', 'multi_link_origin_destination']) and ('origins' not in a) and ('destinations' not in a)]
    #     #     if len(use_existing_od) > 0:
    #     #         for existing in use_existing_od:
    #     #             read_existing = self.config['static'] / 'output_graph' / (existing['name'].replace(' ', '_') + '_graph.gpickle')
    #     #             try:
    #     #                 graph_dict_indirect[existing['name']] = nx.read_gpickle(read_existing)
    #     #                 logging.info(f"Existing graph found in {read_existing}.")
    #     #             except FileNotFoundError as e:
    #     #                 logging.error(f"The graph cannot be found in {read_existing}.", e)
    #     #                 exit()
    #     edges_complex_path = self.network_config['static'] / 'output_graph' / (self.network_name + '_network.p')
    #     G_simple_path = self.network_config['static'] / 'output_graph' / (self.network_name + '_graph.gpickle')
    #
    #     if 'direct' in self.network_config:
    #         try:
    #             with open(edges_complex_path, 'rb') as f:
    #                 edge_gdf = pickle.load(f)
    #                 logging.info(f"Using an existing network: {self.network_name + '_network.p'}")
    #         except FileNotFoundError as e:
    #             logging.error(f"The network cannot be found in {edges_complex_path}.", e)
    #             exit()
    #     if 'indirect' in self.network_config:
    #         try:
    #             G = nx.read_gpickle(G_simple_path)
    #             logging.info(f"Using an existing graph: {self.network_name + '_graph.gpickle'}")
    #         except FileNotFoundError as e:
    #             logging.error(f"The graph cannot be found in {G_simple_path}.", e)
    #             exit()

    # Do the analyses
    if 'direct' in config_analyses:
        analyses_direct.DirectAnalyses(config_analyses).execute()

    if 'indirect' in config_analyses:
        analyses_indirect.IndirectAnalyses(config_analyses).execute()


if __name__ == '__main__':
    main()
