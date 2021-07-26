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
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
import pickle
from shapely.wkt import loads
from osmnx.truncate import truncate_graph_polygon
from osmnx.simplification import simplify_graph
from osmnx.projection import project_geometry
from osmnx.utils_graph import count_streets_per_node
import osmnx.settings as settings
# local modules
from create_network_from_osm_dump import graph_create_unique_ids
from create_network_from_osm_dump import graph_to_gdf


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


def graph_from_polygon(polygon, network_type='all_private',
                       retain_all=True, truncate_by_edge=False, name='unnamed',
                       timeout=180, memory=None,
                       max_query_area_size=50*1000*50*1000,
                       clean_periphery=True, infrastructure='way["highway"]',
                       custom_filter=None, simplify=False):
    """
    Create a networkx graph from OSM data within the spatial boundaries of the
    passed-in shapely polygon.
    This function is based on the osmnx.core.graph_from_polygon function

    Parameters
    ----------
    polygon : shapely Polygon or MultiPolygon
        the shape to get network data within. coordinates should be in units of
        latitude-longitude degrees.
    network_type : string
        what type of street network to get
    simplify : bool is deleted to maintain the complex graph only.
        if true, simplify the graph topology
    retain_all : bool
        if True, return the entire graph even if it is not connected
    truncate_by_edge : bool
        if True retain node if it's outside bbox but at least one of node's
        neighbors are within bbox
    name : string
        the name of the graph
    timeout : int
        the timeout interval for requests and to pass to API
    memory : int
        server memory allocation size for the query, in bytes. If none, server
        will use its default allocation size
    max_query_area_size : float
        max size for any part of the geometry, in square degrees: any polygon
        bigger will get divided up for multiple queries to API
    clean_periphery : bool
        if True (and simplify=True), buffer 0.5km to get a graph larger than
        requested, then simplify, then truncate it to requested spatial extent
    infrastructure : string
        download infrastructure of given type (default is streets
        (ie, 'way["highway"]') but other infrastructures may be selected
        like power grids (ie, 'way["power"~"line"]'))
    custom_filter : string
        a custom network filter to be used instead of the network_type presets

    Returns
    -------
    networkx multidigraph
    """


    # verify that the geometry is valid and is a shapely Polygon/MultiPolygon
    # before proceeding
    if not polygon.is_valid:
        raise TypeError('Shape does not have a valid geometry')
    if not isinstance(polygon, (Polygon, MultiPolygon)):
        raise TypeError('Geometry must be a shapely Polygon or MultiPolygon. If you requested '
                         'graph from place name or address, make sure your query resolves to a '
                         'Polygon or MultiPolygon, and not some other geometry, like a Point. '
                         'See OSMnx documentation for details.')

    if clean_periphery and simplify:
        # create a new buffered polygon 0.5km around the desired one
        buffer_dist = 500
        polygon_utm, crs_utm = project_geometry(geometry=polygon)
        polygon_proj_buff = polygon_utm.buffer(buffer_dist)
        polygon_buffered, _ = project_geometry(geometry=polygon_proj_buff, crs=crs_utm, to_latlong=True)

        # get the network data from OSM,  create the buffered graph, then
        # truncate it to the buffered polygon
        response_jsons = osmnx.downloader._osm_network_download(polygon=polygon_buffered, network_type=network_type,
                                          timeout=timeout, memory=memory,
                                          max_query_area_size=max_query_area_size,
                                          infrastructure=infrastructure, custom_filter=custom_filter)
        G_buffered = osmnx.graph._create_graph(response_jsons, name=name, retain_all=True,
                                  bidirectional=network_type in settings.bidirectional_network_types)

        G_buffered = truncate_graph_polygon(G_buffered, polygon_buffered, retain_all=True, truncate_by_edge=truncate_by_edge)

        # simplify the graph topology
        G_buffered = simplify_graph(G_buffered)

        # truncate graph by polygon to return the graph within the polygon that
        # caller wants. don't simplify again - this allows us to retain
        # intersections along the street that may now only connect 2 street
        # segments in the network, but in reality also connect to an
        # intersection just outside the polygon
        G = truncate_graph_polygon(G_buffered, polygon, retain_all=retain_all, truncate_by_edge=truncate_by_edge)

        # count how many street segments in buffered graph emanate from each
        # intersection in un-buffered graph, to retain true counts for each
        # intersection, even if some of its neighbors are outside the polygon
        G.graph['streets_per_node'] = count_streets_per_node(G_buffered, nodes=G.nodes())

    else:
        # download a list of API responses for the polygon/multipolygon
        response_jsons = osm_net_download(polygon=polygon, network_type=network_type,
                                          timeout=timeout, memory=memory,
                                          max_query_area_size=max_query_area_size,
                                          infrastructure=infrastructure, custom_filter=custom_filter)

        # create the graph from the downloaded data
        G = create_graph(response_jsons, name=name, retain_all=True,
                         bidirectional=network_type in settings.bidirectional_network_types)

        # truncate the graph to the extent of the polygon
        G = truncate_graph_polygon(G, polygon, retain_all=retain_all, truncate_by_edge=truncate_by_edge)
        # add unique identifier for the complex graph
        G = graph_create_unique_ids(G, 'G_complex_fid')

    logging.info('graph_from_polygon() returning graph with {:,} nodes and {:,} edges'.format(len(list(G.nodes())), len(list(G.edges()))))
    return G


def get_graph_from_polygon(InputDict, undirected=True, simplify=True, save_shapes='',save_files=''):
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


    if 'OSM_area_of_interest' in InputDict:
        PathShp = InputDict['OSM_area_of_interest']

    if 'network_type' in InputDict:
        NetworkType = InputDict['network_type']



    with fiona.open(PathShp) as source:
        for r in source:
            if 'geometry' in r:  # added this line to not take into account "None" geometry
                polygon = shape(r['geometry'])
                # wkt = polygon.to_wkt()
                # geom = loads(wkt)
                # polygon, _ = osmnx.projection.project_geometry(polygon, crs={'init': 'epsg:4326'}, to_latlong=True)

    if 'road_types' in InputDict:
        RoadTypes = InputDict['road_types']
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

    if save_shapes:
        graph_to_shp(G_complex, Path(InputDict['output']/(str(InputDict['analysis_name'])+'_G_complex_edges.shp')),
                     Path(InputDict['output']/(str(InputDict['analysis_name'])+'_G_complex_nodes.shp')))


        if simplify:
            graph_to_shp(G_simple, Path(InputDict['output']/(str(InputDict['analysis_name'])+'_G_simple_edges.shp')),
                     Path(InputDict['output']/(str(InputDict['analysis_name'])+'_G_simple_nodes.shp')))

    if save_files:
        path = Path(InputDict['output'] / (str(InputDict['analysis_name'])+'_G_simple.gpickle'))
        nx.write_gpickle(G_simple, path, protocol=4)
        print(path, 'saved')
        path = Path(InputDict['output'] / (str(InputDict['analysis_name'])+'_G_complex.gpickle'))
        nx.write_gpickle(G_complex, path, protocol=4)
        print(path, 'saved')
        edges_complex, node_complex = graph_to_gdf(G_complex)
        with open(str((InputDict['output']) / (str(InputDict['analysis_name'])+'_edges_complex.p')), 'wb') as handle:
            pickle.dump(edges_complex, handle)
            print(str((InputDict['output']) / (str(InputDict['analysis_name'])+'_edges_complex.p saved')))
    return G_complex, G_simple

def from_polygon_tool_workflow(InputDict, save_shapes= '', save_files=''):
    """
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
    ra2ce_main_path = Path(__file__).parents[1]
    G_complex, G_simple =get_graph_from_polygon(InputDict, save_shapes=save_shapes, save_files=save_files)

    #CONVERT GRAPHS TO GEODATAFRAMES
    print('Start converting the graphs to geodataframes')
    edges_complex, nodes_complex = graph_to_gdf(G_complex)
    edges_simple, nodes_simple = graph_to_gdf(G_simple)
    print('Finished converting the graphs to geodataframes')

    return G_simple, edges_complex

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

    G_simple, edges_complex = from_polygon_tool_workflow(InputDict)

    print("Ran create_network_from_polygon.py successfully!")
