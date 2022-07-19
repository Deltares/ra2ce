# -*- coding: utf-8 -*-
"""
Created on 18-7-2022

@author: F.C. de Groen, Deltares
"""
# Import modules
import networkx as nx
import geopandas as gpd
import pickle
import logging

# Import local modules
from .graph.networks_utils import graph_to_shp


def read_gpickle(path):
    with open(path, 'rb') as f:
        g = pickle.load(f)
    return g


def read_graphs(config):
    graphs = {}
    for input_graph in ['base_graph', 'origins_destinations_graph']:
        # Load graphs
        filename = config['static'] / 'output_graph' / f'{input_graph}.p'
        if filename.is_file():
            graphs[input_graph] = read_gpickle(filename)
        else:
            graphs[input_graph] = None

        filename = config['static'] / 'output_graph' / f'{input_graph}_hazard.p'
        if filename.is_file():
            graphs[input_graph + '_hazard'] = read_gpickle(filename)
        else:
            graphs[input_graph + '_hazard'] = None

    # Load networks
    filename = config['static'] / 'output_graph' / f'base_network.feather'
    if filename.is_file():
        graphs['base_network'] = gpd.read_feather(filename)
    else:
        graphs['base_network'] = None

    filename = config['static'] / 'output_graph' / f'base_network_hazard.feather'
    if filename.is_file():
        graphs['base_network_hazard'] = gpd.read_feather(filename)
    else:
        graphs['base_network_hazard'] = None

    return graphs


def save_network(to_save, output_folder, name, types=['pickle']):
    """Saves a geodataframe or graph to output_path
    TODO: add encoding to ini file to make output more flexible

        Args:

        Returns:

    """
    if type(to_save) == gpd.GeoDataFrame:
        # The file that needs to be saved is a geodataframe
        if 'pickle' in types:
            output_path_pickle = output_folder / (name + '.feather')
            to_save.to_feather(output_path_pickle, index=False)
            logging.info(f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}.")
        if 'shp' in types:
            output_path = output_folder / (name + '.shp')
            to_save.to_file(output_path, index=False)  #, encoding='utf-8' -Removed the encoding type because this causes some shapefiles not to save.
            logging.info(f"Saved {output_path.stem} in {output_path.resolve().parent}.")
        return output_path_pickle

    elif type(to_save) == nx.classes.multigraph.MultiGraph or type(to_save) == nx.classes.multidigraph.MultiDiGraph:
        # The file that needs to be saved is a graph
        if 'shp' in types:
            graph_to_shp(to_save, output_folder / (name + '_edges.shp'),
                         output_folder / (name + '_nodes.shp'))
            logging.info(f"Saved {name + '_edges.shp'} and {name + '_nodes.shp'} in {output_folder}.")
        if 'pickle' in types:
            output_path_pickle = output_folder / (name + '.p')
            with open(output_path_pickle, 'wb') as f:
                pickle.dump(to_save, f, protocol=4)
            logging.info(f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}.")
        return output_path_pickle
    else:
        return None


def save_linking_tables(destination_folder, simple_to_complex, complex_to_simple):
    """
    Function that save the tables that link the simple and complex graph/netwok

    Arguments:
        *simple_to_complex* (dict) : keys: ids of simple graph; values: matching ids of complex graph [list]
        *complex_to_simple* (dict) : keys: ids of complex graph; values: matching ids of simple graph [int]

    Returns:
        None

    Effect: saves the lookup tables as json files in the static/output_graph folder

    """

    # save lookup table if necessary
    import json

    if not destination_folder.exists():
        destination_folder.mkdir()

    with open((destination_folder / 'simple_to_complex.json'), 'w') as fp:
        json.dump(simple_to_complex, fp)
        logging.info('saved (or overwrote) simple_to_complex.json')
    with open((destination_folder /'complex_to_simple.json'), 'w') as fp:
        json.dump(complex_to_simple, fp)
        logging.info('saved (or overwrote) complex_to_simple.json')

