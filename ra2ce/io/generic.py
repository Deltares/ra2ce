# -*- coding: utf-8 -*-

import logging
import pickle

import geopandas as gpd

# Import modules
import networkx as nx

# Import local modules
from ra2ce.graph.networks_utils import graph_to_shp


def save_network(to_save, output_folder, name, types=["pickle"]):
    """Saves a geodataframe or graph to output_path
    TODO: add encoding to ini file to make output more flexible

        Args:

        Returns:

    """
    raise NotImplementedError("Phased Out")
