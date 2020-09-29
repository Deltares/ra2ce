# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 09:50:42 2019

@author: Frederique de Groen

Part of a general tool for criticality analysis of networks.

"""
# modules
import pandas as pd
import network_functions_v2 as nf
import os
import time
import logging

LOG_FILENAME = './logs/log_file.log'
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)


# types of analyses
def single_link_alternative_routes(name, AllOutput, InputDataDict, crs, snapping, SnappingThreshold, pruning, PruningThreshold):
    """
    This is the function to analyse roads with a single link disruption and
    an alternative route.

    Arguments:
        AllOutput [string] = path where the output shapefiles should be saved
        InputDataDict [dictionary] = dictionary of input data used for calculating
            the costs for taking alternative routes
        ParameterNamesDict [dictionary] = names of the parameters used for calculating
            the costs for taking alternative routes
    """
    logging.info("----------------------------- {} -----------------------------".format(name))
    startstart = time.time()

    print("\nYou have chosen the Single Link Alternative Route Finder. You might need to give a bit more input later. Starting to calculate now...\n")

    if 'id_name' in InputDataDict:
        id_name = InputDataDict['id_name']

    if 'road_usage_data_path' in InputDataDict:
        road_usage_data = pd.read_excel(InputDataDict['road_usage_data_path'])
        road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
    else:
        aadt_names = None
        road_usage_data = pd.DataFrame()

    G = create_graph_from_shapefiles(name, AllOutput, InputDataDict, None, crs, snapping, SnappingThreshold, pruning, PruningThreshold)

    # CALCULATE CRITICALITY
    gdf = nf.criticality_single_link(G, id_name, roadUsageData=road_usage_data, aadtNames=aadt_names)
    logging.info("Function [criticality_single_link]: executing")

    # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
    # todo: input here this option

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [single_link_alternative_routes]: {}".format(nf.timer(startstart, end)))


def single_link_alternative_routes_graph(name, AllOutput, graph, crs):
    """
    This is the function to analyse roads with a single link disruption calculating
    an alternative route. The input is a graph that is downloaded from OSM.
    """
    logging.info("----------------------------- {} -----------------------------".format(name))
    print("\nExecuting analysis..")

    startstart = time.time()

    # save the graph as a shapefile
    nf.graph_to_shp(graph, os.path.join(AllOutput, '{}_edges.shp'.format(name)),
                    os.path.join(AllOutput, '{}_nodes.shp'.format(name)))

    # CALCULATE CRITICALITY
    gdf = nf.criticality_single_link_osm(graph)  # TODO: input the type of roads to analyse
    logging.info("Function [criticality_single_link]: executing for {}".format(name))

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [single_link_alternative_routes]: {}".format(nf.timer(startstart,end)))


def multi_link_alternative_routes(name, AllOutput, InputDataDict, HazardDataDict, crs, snapping, SnappingThreshold, pruning, PruningThreshold):
    """
    This is the function to analyse roads with a multi link disruption calculating
    an alternative route.
    """

    logging.info("----------------------------- {} -----------------------------".format(name))
    startstart = time.time()

    print(
        "\nYou have chosen the Multi-link Disruption Alternative Route Finder. You might need to give a bit more input later. Starting to calculate now...\n")

    # initiate variables
    id_name_hazard = None

    # load the input files if they are there
    if 'id_name' in InputDataDict:
        id_name = InputDataDict['id_name']

    if HazardDataDict:
        # there is hazard data available
        if 'ID' in HazardDataDict:
            id_name_hazard = HazardDataDict['ID']

    G = create_graph_from_shapefiles(name, AllOutput, InputDataDict, HazardDataDict, crs, snapping, SnappingThreshold, pruning,
                                     PruningThreshold)

    if (id_name_hazard is None) & (len(HazardDataDict) != 0):
        G = nf.hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # CALCULATE CRITICALITY
    gdf = nf.criticality_multi_link_hazard(G, HazardDataDict['attribute_name'], HazardDataDict['threshold'])
    logging.info("Function [criticality_single_link]: executing")

    # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
    # todo: input here this option

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_alternative_routes]: {}".format(nf.timer(startstart, end)))


def multi_link_alternative_routes_graph(name, AllOutput, graph, crs, HazardDataDict):
    """Calculates if road segments that are disrupted have an alternative route from node to node
    Args:

    Returns:

    """

    logging.info("----------------------------- {} -----------------------------".format(name))
    startstart = time.time()

    print(
        "\nYou have chosen the Multi-link Disruption: Calculate the disruption for all damaged roads. Starting to calculate now...\n")

    # initiate variables
    id_name = 'osmid'

    # intersect graph with hazard data
    graph = nf.hazard_intersect_graph(graph, HazardDataDict['path'], HazardDataDict['attribute_name'],
                                      name, agg=HazardDataDict['aggregation'])

    # CALCULATE CRITICALITY
    gdf = nf.criticality_multi_link_hazard(graph, HazardDataDict['attribute_name'], HazardDataDict['threshold'], id_name)

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_alternative_routes_graph]: {}".format(nf.timer(startstart, end)))


def single_link_access_routes():
    """
    This is the function to analyse roads with a single link disruption calculating
    the accessibility of points of interest.
    """
    print("The function has not been implemented yet..\n")


def multi_link_access_routes():
    """
    This is the function to analyse roads with a multi link disruption calculating
    an accessibility of points of interest.
    """
    print("The function has not been implemented yet..\n")


def single_link_europe(graph, AllOutput, name, crs):
    print("Calculating the criticality...\n")
    gdf = nf.criticality_single_link_osm(graph, ['motorway', 'motorway_link'])
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))


def multi_link_od_matrix(name, AllOutput, InputDataDict, HazardDataDict, crs, snapping, SnappingThreshold, pruning, PruningThreshold):
    """
    Removes all links that are disrupted by a hazard. It takes
    an Origin/Destination matrix as input and calculates the alternative routes for
    each O/D pair, if links are removed between the fastest route from O to D.

    Arguments:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        AllOutput [string] = path where the output shapefiles should be saved
        InputDataDict [dictionary] = dictionary of input data used for calculating
            the costs for taking alternative routes
        HazardDataDict [dictionary] = information of hazard data
    """

    logging.info("----------------------------- {} -----------------------------".format(name))
    startstart = time.time()

    print("\nYou have chosen the Multi-link Disruption Analysis - to calculate the disruption for an Origin/Destination. You might need to give a bit more input later. Starting to calculate now...\n")

    # initiate variables
    id_name_hazard = None
    weighing = 'distance'  # TODO: make this variable

    # load the input files if they are there
    if 'id_name' in InputDataDict:
        id_name = InputDataDict['id_name']

    if HazardDataDict:
        # there is hazard data available
        if 'ID' in HazardDataDict:
            id_name_hazard = HazardDataDict['ID']

    G = create_graph_from_shapefiles(name, AllOutput, InputDataDict, HazardDataDict, crs, snapping, SnappingThreshold, pruning,
                                     PruningThreshold)

    if (id_name_hazard is None) & (len(HazardDataDict) != 0):
        G = nf.hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # Add the origin/destination nodes to the network
    ods = nf.read_OD_files(InputDataDict['origin_shapefiles_path'], InputDataDict['o_names'],
                           InputDataDict['destination_shapefiles_path'], InputDataDict['d_names'],
                           InputDataDict['id_od'], crs)

    # Check if the ID's are unique per edge: if not, add an own ID called 'fid'
    if len(set([str(e[-1][id_name]) for e in G.edges.data(keys=True)])) < len(G.edges()):
        i = 0
        for u, v, k in G.edges(keys=True):
            G[u][v][k]['fid'] = i
            i += 1
        print(
            "Added a new unique identifier field 'fid' because the original field '{}' did not contain unique values per road segment.".format(
                id_name))
        id_name = 'fid'

    ods = nf.create_OD_pairs(ods, G, id_name)
    G = nf.add_od_nodes(G, ods, id_name, name=name, file_output=AllOutput, save_shp=True)

    if weighing == 'time':
        # not yet possible for input with shapefiles, except when a max speed attribute is attached to the shapefile
        # calculate the time it takes per road segment
        avg_speeds = nf.calc_avg_speed(G, 'highway', save_csv=True, save_path=os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        avg_speeds = pd.read_csv(os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        if len(avg_speeds.loc[avg_speeds['avg_speed'] == 0]) > 0:
            logging.info("An average speed of 50 is used in locations where the maximum speed limit is 0 in OSM data.")
            avg_speeds.loc[avg_speeds['avg_speed'] == 0, 'avg_speed'] = 50  # this is assumed
        G = nf.assign_avg_speed(G, avg_speeds, 'highway')

        # make a time value of seconds, length of road streches is in meters
        for u, v, k, edata in G.edges.data(keys=True):
            hours = (edata['length'] / 1000) / edata['avgspeed']
            G[u][v][k][weighing] = hours * 3600

    # Calculate the preferred routes
    pref_routes = nf.preferred_routes_od(G, weighing, id_name, ods, crs, HazardDataDict, shortest_route=True, save_shp=True, save_pickle=False,
                                         file_output=AllOutput, name=name)

    # Calculate the criticality
    gdf = nf.criticality_multi_link_hazard_OD(G, pref_routes, weighing, HazardDataDict['attribute_name'][0],
                                              HazardDataDict['threshold'], crs)

    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_od_matrix]: {}".format(nf.timer(startstart, end)))


def multi_link_od_matrix_graph(name, AllOutput, InputDataDict, HazardDataDict, G, crs):
    """
    Removes all links that are disrupted by a hazard. It takes
    an Origin/Destination matrix as input and calculates the alternative routes for
    each O/D pair, if links are removed between the fastest route from O to D.

    Arguments:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        AllOutput [string] = path where the output shapefiles should be saved
        InputDataDict [dictionary] = dictionary of input data used for calculating
            the costs for taking alternative routes
        HazardDataDict [dictionary] = information of hazard data
    """
    logging.info("----------------------------- {} -----------------------------".format(name))
    startstart = time.time()

    print("\nYou have chosen the Multi-link Disruption Analysis - to calculate the disruption for an Origin/Destination. You might need to give a bit more input later. Starting to calculate now...\n")

    # initiate variables
    id_name_hazard = None
    weighing = 'distance'  # TODO: make this variable

    # load the input files if they are there
    id_name = 'osmid'  # this is always osmid for a graph from OSM

    if HazardDataDict:
        # there is hazard data available
        if 'ID' in HazardDataDict:
            id_name_hazard = HazardDataDict['ID']

    # not all edges contain the attribute 'geometry' - because of geometry simplification these are streets that are straight and can be computed
    G = nf.add_missing_geoms_graph(G)

    if (id_name_hazard is None) & (len(HazardDataDict) != 0):
        G = nf.hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # Add the origin/destination nodes to the network
    ods = nf.read_OD_files(InputDataDict['origin_shapefiles_path'], InputDataDict['o_names'],
                           InputDataDict['destination_shapefiles_path'], InputDataDict['d_names'],
                           InputDataDict['id_od'], crs)

    # Check if the ID's are unique per edge: if not, add an own ID called 'fid'
    if len(set([str(e[-1][id_name]) for e in G.edges.data(keys=True)])) < len(G.edges()):
        i = 0
        for u, v, k in G.edges(keys=True):
            G[u][v][k]['fid'] = i
            i += 1
        print(
            "Added a new unique identifier field 'fid' because the original field '{}' did not contain unique values per road segment.".format(
                id_name))
        id_name = 'fid'

    ods = nf.create_OD_pairs(ods, G, id_name)
    G = nf.add_od_nodes(G, ods, id_name, name=name, file_output=AllOutput, save_shp=True)

    if weighing == 'time':
        # calculate the time it takes per road segment
        avg_speeds = nf.calc_avg_speed(G, 'highway', save_csv=True, save_path=os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        avg_speeds = pd.read_csv(os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        if len(avg_speeds.loc[avg_speeds['avg_speed'] == 0]) > 0:
            logging.info("An average speed of 50 is used in locations where the maximum speed limit is 0 in OSM data.")
            avg_speeds.loc[avg_speeds['avg_speed'] == 0, 'avg_speed'] = 50  # this is assumed
        G = nf.assign_avg_speed(G, avg_speeds, 'highway')

        # make a time value of seconds, length of road streches is in meters
        for u, v, k, edata in G.edges.data(keys=True):
            hours = (edata['length'] / 1000) / edata['avgspeed']
            G[u][v][k][weighing] = hours * 3600

    # Calculate the preferred routes
    pref_routes = nf.preferred_routes_od(G, weighing, id_name, ods, crs, HazardDataDict, shortest_route=True, save_shp=True, save_pickle=False,
                                         file_output=AllOutput, name=name)

    # Calculate the criticality
    gdf = nf.criticality_multi_link_hazard_OD(G, pref_routes, weighing, HazardDataDict['attribute_name'][0],
                                              HazardDataDict['threshold'], crs)

    # save graph
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    nf.gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_od_matrix_graph]: {}".format(nf.timer(startstart, end)))


# Graph creation from shapefile(s)
def create_graph_from_shapefiles(name, AllOutput, InputDataDict, HazardDataDict, crs, snapping, SnappingThreshold, pruning, PruningThreshold):
    # initiate variables
    shapefile_diversion = 0
    id_name_hazard = None

    # load the input files if they are there
    if 'id_name' in InputDataDict:
        id_name = InputDataDict['id_name']

    if 'shapefiles_for_analysis_path' in InputDataDict:
        shapefile_analyse = InputDataDict['shapefiles_for_analysis_path']

    if 'shapefiles_for_diversion_path' in InputDataDict:
        shapefile_diversion = InputDataDict['shapefiles_for_diversion_path']

    if 'road_usage_data_path' in InputDataDict:
        road_usage_data = pd.read_excel(InputDataDict['road_usage_data_path'])
        road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
    else:
        aadt_names = None
        road_usage_data = pd.DataFrame()

    if HazardDataDict:
        # there is hazard data available
        if 'ID' in HazardDataDict:
            id_name_hazard = HazardDataDict['ID']

    # Load shapefile
    lines = nf.read_merge_shp(shapefileAnalyse=shapefile_analyse,
                              shapefileDiversion=shapefile_diversion,
                              idName=id_name,
                              crs_=crs)
    logging.info("Function [read_merge_shp]: executed with {} {}".format(shapefile_analyse, shapefile_diversion))

    # Multilinestring to linestring
    # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
    # The list of fid's is reduced by the fid's that are not anymore in the merged lines
    edges, lines_merged = nf.merge_lines_shpfiles(lines, id_name, aadt_names, crs)
    logging.info("Function [merge_lines_shpfiles]: executed with properties {}".format(list(edges.columns)))

    if snapping:
        edges = nf.snap_endpoints_lines(edges, SnappingThreshold, id_name, tolerance=1e-7)
        logging.info("Function [snap_endpoints_lines]: executed with threshold = {}".format(SnappingThreshold))
        # TODO: when lines are added the properties cannot be saved well - this should be integrated

    # TODO
    #    if pruning:
    #        lines = nf.prune_lines(lines, prune_threshold=PruningThreshold)

    # merge merged lines if there are any merged lines
    if not lines_merged.empty:
        # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
        lines_merged.to_file(os.path.join(AllOutput, "{}_lines_that_merged.shp".format(name)))
        logging.info(
            "Function [edges_to_shp]: saved at {}".format(os.path.join(AllOutput, "{}_lines_that_merged".format(name))))

    # Get the unique points at the end of lines and at intersections to create nodes
    nodes = nf.create_nodes(edges, crs)
    logging.info("Function [create_nodes]: executed")

    if snapping:
        # merged lines may be updated when new nodes are created which makes a line cut in two
        edges = nf.cut_lines(edges, nodes, id_name, tolerance=1e-4)
        nodes = nf.create_nodes(edges, crs)
        logging.info("Function [cut_lines]: executed")

    # save the merged lines (correct edges) as shapefile
    edges.to_file(os.path.join(AllOutput, '{}_edges.shp'.format(name)))
    logging.info("Function [edges_to_shp]: executed for '{}_edges'".format(name))

    # save the intersection points as shapefile
    nodes.to_file(os.path.join(AllOutput, '{}_nodes.shp'.format(name)))
    logging.info("Function [nodes_to_shp]: executed for '{}_nodes'".format(name))

    if id_name_hazard is not None:
        # there is hazard data available
        edges = nf.hazard_join_id_shp(edges, HazardDataDict)

    # create tuples from the adjecent nodes and add as column in geodataframe
    resulting_network = nf.join_nodes_edges(nodes, edges, id_name)
    logging.info("Function [join_nodes_edges]: executed")

    # save geodataframe to shapefile
    resulting_network.crs = {'init': 'epsg:{}'.format(crs)}  # set the right CRS
    resulting_network.to_file(os.path.join(AllOutput, '{}_resulting_network.shp'.format(name)))

    # Create networkx graph from geodataframe
    G = nf.graph_from_gdf(resulting_network, nodes)
    logging.info("Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(name))

    return G