# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

# external modules
import networkx as nx
import osmnx
from pathlib import Path
from numpy import object as np_object
from shapely.geometry import shape
import logging
import fiona
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
import pickle
from shapely.wkt import loads
from osmnx.truncate import truncate_graph_polygon
from osmnx.simplification import simplify_graph
from osmnx.projection import project_geometry
from osmnx.utils_graph import count_streets_per_node
import osmnx.settings as settings


class Network:
    def __init__(self, config):
        self.config = config
        self.save_shp = True if config['network']['save_shp'] == 'true' else False
        self.save_csv = True if config['network']['save_csv'] == 'true' else False

    def network_shp(self):
        """Creates a network from a shapefile."""
        return

    def network_osm_pbf(self):
        """Creates a network from an OSM PBF file."""
        return

    def network_osm_download(self):
        """Creates a network from a polygon by downloading via the OSM API in the extent of the polygon.
        Example workflow for use in the tool version of RA2CE

        Arguments:
            *InputDict* (Path) with
            PathShp [string]: path to shapefile (polygon) used to download from OSMnx the roads in that polygon
            NetworkType [string]: one of the network types from OSM, e.g. drive, drive_service, walk, bike, all
            RoadTypes [string]: formatted like "motorway|primary", one or multiple road types from OSM (highway)
            undirected is True, unless specified as False
            simplify graph is True, unless specified as False
            save_shapes is False, unless you would like to save shapes of both graphs

        Returns:
            G_simple (Graph) : Simplified graph (for use in the indirect analyses)
            G_complex_edges (GeoDataFrame : Complex graph (for use in the direct analyses)
        """
        # ra2ce_main_path = Path(__file__).parents[1]
        G_complex, G_simple = get_graph_from_polygon(self.config, save_shp=self.save_shp, save_csv=self.save_csv)

        # CONVERT GRAPHS TO GEODATAFRAMES
        print('Start converting the graphs to geodataframes')
        # edges_complex, nodes_complex = graph_to_gdf(G_complex)
        # edges_simple, nodes_simple = graph_to_gdf(G_simple)
        print('Finished converting the graphs to geodataframes')

        return G_simple  #, edges_complex

    def add_od_nodes(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        return

    def save_network(self):
        return

    def create(self):
        """Function with the logic to call the right analyses."""
        return


class Hazard:
    def __init__(self):
        self.something = 'bla'

    def overlay_hazard_raster(self):
        """Overlays the hazard raster over the road segments."""
        return

    def overlay_hazard_shp(self):
        """Overlays the hazard shapefile over the road segments."""
        return

    def join_hazard_table(self):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        return


def get_graph_from_polygon(config, undirected=True, simplify=True, save_shp='', save_csv=''):
    """
    Get an OSMnx graph from a polygon shapefile .

    Args:
        Input Dict with
        PathShp [string]: path to shapefile (polygon) used to download from OSMnx the roads in that polygon
        NetworkType [string]: one of the network types from OSM, e.g. drive, drive_service, walk, bike, all
        RoadTypes [string]: formatted like "motorway|primary", one or multiple road types from OSM (highway)
        undirected is True, unless specified as False
        simplify graph is True, unless specified as False
        save_shapes is False, unless you would like to save shapes of both graphs
    Returns:
        G [networkx multidigraph complex]
        G [networkx multidigraph simple] when simplify is True


    """

    if 'polygon' in config['network']:
        PathShp = config['network']['polygon']

    if 'network_type' in config['network']:
        NetworkType = config['network']['network_type']

    with fiona.open(PathShp) as source:
        for r in source:
            if 'geometry' in r:  # added this line to not take into account "None" geometry
                polygon = shape(r['geometry'])
                # wkt = polygon.to_wkt()
                # geom = loads(wkt)
                # polygon, _ = osmnx.projection.project_geometry(polygon, crs={'init': 'epsg:4326'}, to_latlong=True)

    if 'road_types' in config['network']:
        RoadTypes = config['network']['road_types']
        cf = ('["highway"~"{}"]'.format(RoadTypes))
        print(cf)
        # assuming the empty cell in the excel is a numpy.float64 nan value
        #osmnx 0.16/1.01

        G_complex = osmnx.graph_from_polygon(polygon=polygon, custom_filter=cf, simplify=False, retain_all=True)
        # osmnx OLD
        # G_complex = graph_from_polygon(polygon=polygon, network_type=NetworkType,infrastructure='way["highway"~"motorway|trunk|primary"]', simplify=False)
    else:
        G_complex = osmnx.graph_from_polygon(polygon=polygon, network_type=NetworkType, simplify=False, retain_all=True)

    # simplify the graph topology as the last step.
    if simplify:
        G_simple = simplify_graph(G_complex)
        G_simple = graph_create_unique_ids(G_simple, 'G_simple_fid')
        print('graphs_from_o5m() returning graph with {:,} nodes and {:,} edges'.format(len(list(G_simple.nodes())),
                                                                                        len(list(G_simple.edges()))))
    else:
        G_simple = None
        print('Did not create a simplified version of the graph')

    # we want to use undirected graphs, so turn into an undirected graph
    if undirected:
        if type(G_complex) == nx.classes.multidigraph.MultiDiGraph:
            G_complex = G_complex.to_undirected()
        if type(G_simple) == nx.classes.multidigraph.MultiDiGraph:
            G_simple = G_simple.to_undirected()

    return G_complex, G_simple


def graph_create_unique_ids(graph,new_id_name):
    #Tip: if you use enumerate(), you don't have to make a seperate i-counter


    # Check if new_id_name exists and if unique
    #else  create new_id_name
    # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
    #
    # else:
        i = 0
        for u, v, k in graph.edges(keys=True):
            graph[u][v][k][new_id_name] = i
            i += 1
        print(
            "Added a new unique identifier field {}.".format(
                new_id_name))
        return graph
    # else:
    #     return graph, new_id_name


def graph_to_gdf(G):
    """Takes in a networkx graph object and returns edges and nodes as geodataframes
    Arguments:
        G (Graph): networkx graph object to be converted

    Returns:
        edges (GeoDataFrame) : containes the edges
        nodes (GeoDataFrame) :
    """
    # now only multidigraphs and graphs are used
    if type(G) == nx.classes.graph.Graph:
        G = nx.MultiGraph(G)

    nodes, edges = osmnx.graph_to_gdfs(G)

    dfs = [edges, nodes]
    for df in dfs:
        for col in df.columns:
            if df[col].dtype == np_object and col != df.geometry.name:
                df[col] = df[col].astype(str)

    return edges, nodes