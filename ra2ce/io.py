# -*- coding: utf-8 -*-
"""
Created on 18-7-2022

@author: F.C. de Groen, Deltares
"""

import networkx as nx
import geopandas as gpd


def read_graphs(config):
    graphs = {}
    for input_graph in ['base_graph', 'origins_destinations_graph']:
        # Load graphs
        filename = config['static'] / 'output_graph' / f'{input_graph}.gpickle'
        if filename.is_file():
            graphs[input_graph] = nx.read_gpickle(filename)
        else:
            graphs[input_graph] = None

        filename = config['static'] / 'output_graph' / f'{input_graph}_hazard.gpickle'
        if filename.is_file():
            graphs[input_graph + '_hazard'] = nx.read_gpickle(filename)
        else:
            graphs[input_graph + '_hazard'] = None

    # Load networks
    filename = config['static'] / 'output_graph' / f'base_network.p'
    if filename.is_file():
        graphs['base_network'] = gpd.read_feather(filename)
    else:
        graphs['base_network'] = None

    filename = config['static'] / 'output_graph' / f'base_network_hazard.p'
    if filename.is_file():
        graphs['base_network_hazard'] = gpd.read_feather(filename)
    else:
        graphs['base_network_hazard'] = None

    return graphs
