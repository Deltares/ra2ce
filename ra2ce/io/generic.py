# -*- coding: utf-8 -*-
"""
Created on 18-7-2022
"""
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
    if type(to_save) == gpd.GeoDataFrame:
        # The file that needs to be saved is a geodataframe
        if "pickle" in types:
            output_path_pickle = output_folder / (name + ".feather")
            to_save.to_feather(output_path_pickle, index=False)
            logging.info(
                f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}."
            )
        if "shp" in types:
            output_path = output_folder / (name + ".shp")
            to_save.to_file(
                output_path, index=False
            )  # , encoding='utf-8' -Removed the encoding type because this causes some shapefiles not to save.
            logging.info(f"Saved {output_path.stem} in {output_path.resolve().parent}.")
        return output_path_pickle

    elif (
        type(to_save) == nx.classes.multigraph.MultiGraph
        or type(to_save) == nx.classes.multidigraph.MultiDiGraph
    ):
        # The file that needs to be saved is a graph
        if "shp" in types:
            graph_to_shp(
                to_save,
                output_folder / (name + "_edges.shp"),
                output_folder / (name + "_nodes.shp"),
            )
            logging.info(
                f"Saved {name + '_edges.shp'} and {name + '_nodes.shp'} in {output_folder}."
            )
        if "pickle" in types:
            output_path_pickle = output_folder / (name + ".p")
            with open(output_path_pickle, "wb") as f:
                pickle.dump(to_save, f, protocol=4)
            logging.info(
                f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}."
            )
        return output_path_pickle
    else:
        return None
