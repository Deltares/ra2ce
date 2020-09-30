# -*- coding: utf-8 -*-
"""
Created on Thu May 16 17:09:19 2019

@author: Frederique de Groen

Part of a general tool for criticality analysis of networks.

"""
''' MODULES '''
import networkx as nx
import osmnx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import geopandas as gpd
import itertools
import os, sys
import logging
import rtree
import pickle
import rasterio
import fiona
from fiona.crs import from_epsg
from shapely.geometry import mapping, Point, LineString, shape, MultiLineString, Polygon, MultiPolygon
from shapely.ops import linemerge, unary_union
from shapely.wkt import loads
from prettytable import PrettyTable
from statistics import mean
from numpy import object as np_object
from geopy import distance


def get_graph_from_polygon(PathShp, NetworkType, RoadTypes=None):
    """
    Get an OSMnx graph from a shapefile (input = path to shapefile).

    Args:
        PathShp [string]: path to shapefile (polygon) used to download from OSMnx the roads in that polygon
        NetworkType [string]: one of the network types from OSM, e.g. drive, drive_service, walk, bike, all
        RoadTypes [string]: formatted like "motorway|primary", one or multiple road types from OSM (highway)

    Returns:
        G [networkx multidigraph]
    """
    with fiona.open(PathShp) as source:
        for r in source:
            if 'geometry' in r:  # added this line to not take into account "None" geometry
                polygon = shape(r['geometry'])

    if RoadTypes == RoadTypes:
        # assuming the empty cell in the excel is a numpy.float64 nan value
        G = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType, infrastructure='way["highway"~"{}"]'.format(RoadTypes))
    else:
        G = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType)

    # we want to use undirected graphs, so turn into an undirected graph
    if type(G) == nx.classes.multidigraph.MultiDiGraph:
        G = G.to_undirected()

    return G
