# -*- coding: utf-8 -*-
"""
Created on 28-10-2020

@authors:
Margreet van Marle (margreet.vanmarle@deltares.nl)
Frederique de Groen (frederique.degroen@deltares.nl)
"""
# external modules
import networkx as nx
import osmnx
from pathlib import Path
from numpy import object as np_object
from shapely.geometry import shape
import logging
import fiona

# local modules
from utils import load_config


LOG_FILENAME = './logs/log_create_network_from_poly.log'
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

root = Path(__file__).parents[2]
AllOutput = root / Path(load_config()['paths']['test_output'])
AllInput = root / Path(load_config()['paths']['test_area_of_interest'])

def graph_to_shp(G, edge_shp, node_shp):
    """Takes in a networkx graph object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:

        G []: networkx graph object to be converted

        edge_shp [str]: output path including extension for edges shapefile

        node_shp [str]: output path including extension for nodes shapefile

    Returns:

        None

    """
    # now only multidigraphs and graphs are used
    if type(G) == nx.classes.graph.Graph:
        G = nx.MultiGraph(G)

    # The nodes should have a geometry attribute (perhaps on top of the x and y attributes)
    nodes, edges = osmnx.graph_to_gdfs(G)

    dfs = [edges, nodes]
    for df in dfs:
        for col in df.columns:
            if df[col].dtype == np_object and col != df.geometry.name:
                df[col] = df[col].astype(str)

    print('\nSaving nodes as shapefile: {}'.format(node_shp))
    print('\nSaving edges as shapefile: {}'.format(edge_shp))

    nodes.to_file(node_shp, driver='ESRI Shapefile', encoding='utf-8')
    edges.to_file(edge_shp, driver='ESRI Shapefile', encoding='utf-8')

def get_graph_from_polygon(InputDict):
    """
    Get an OSMnx graph from a shapefile (input = path to shapefile).

    Args:
        PathShp [string]: path to shapefile (polygon) used to download from OSMnx the roads in that polygon
        NetworkType [string]: one of the network types from OSM, e.g. drive, drive_service, walk, bike, all
        RoadTypes [string]: formatted like "motorway|primary", one or multiple road types from OSM (highway)

    Returns:
        G [networkx multidigraph]
    """
    if 'OSM_area_of_interest' in InputDict:
        PathShp = AllInput / InputDict['OSM_area_of_interest']
    # PathShp=r"C:\Users\Marle\RunningProjects\KBN_RegionaleOverstromingen\ra2ce\test\input\area_of_interest\zuidholland_WGS84.shp"

    if 'network_type' in InputDict:
        NetworkType = InputDict['network_type']

    if 'road_types' in InputDict:
          RoadTypes = InputDict['road_types']
    # RoadTypes="motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link"

    with fiona.open(PathShp) as source:
        for r in source:
            if 'geometry' in r:  # added this line to not take into account "None" geometry
                polygon = shape(r['geometry'])

    if RoadTypes == RoadTypes:
        # assuming the empty cell in the excel is a numpy.float64 nan value
        #osmnx 0.16
        #G = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType, custom_filter='["highway"~"{}"]'.format(RoadTypes))
        G = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType,infrastructure='way["highway"~"{}"]'.format(RoadTypes))
    else:
        G = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType)

    # we want to use undirected graphs, so turn into an undirected graph
    if type(G) == nx.classes.multidigraph.MultiDiGraph:
        G = G.to_undirected()

    return G

if __name__ == '__main__':

    # General test input
    input_crs = 4326  # the Coordinate Reference System of the input shapefiles should be in EPSG:4326 because OSM always uses this CRS

    # Test specific test input
    InputDict = {'analysis_name': 'zuidholland',
                      'analysis': 'Redundancy-based criticality',
                      'links_analysis': 'Single-link Disruption',
                      'network_source': 'Network based on OSM online',
                      'OSM_area_of_interest': 'zuidholland_WGS84.shp',
                      'network_type': 'drive',
                      'road_types': 'motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link'}

    G = get_graph_from_polygon(InputDict)

    # Save graph to shapefile for visual inspection
    graph_to_shp(G, Path(AllOutput).joinpath('{}_edges.shp'.format(InputDict['analysis_name'])),
                 Path(AllOutput).joinpath('{}_nodes.shp'.format(InputDict['analysis_name'])))
    # graph = get_graph_from_polygon(r"C:\Users\Marle\RunningProjects\KBN_RegionaleOverstromingen\ra2ce\test\input\area_of_interest\zuidholland.shp", "drive", "motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link")


    print("Ran create_network_from_poly.py successfully!")
