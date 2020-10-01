# -*- coding: utf-8 -*-
"""
Created on 1-10-2020

@authors:
create_network_from_shapefile: Frederique de Groen (frederique.degroen@deltares.nl)
"""

# external modules
import pandas as pd
import os
import time
import logging

LOG_FILENAME = './logs/log_file.log'
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

# TODO check if it appends a unique ID if the ID name/column that is in the input is not unique (for shp and OSM both)
# TODO make the file in the order:
#   - create network and/or graph
#   - do the analysis


def read_input_analyse(FolderModelInput, FolderModelOutput, RootFolder, NameInputExcel, batch=False):
    """
    This function reads the input excel and points to the right analysis.
    FolderModelInput: full path of the folder where the model input is stored.
    FolderModelOutput: full path of the folder where the model output should be stored.
    """
    # Ask the user for the name of the analysis
    if not batch:
        input_name = input("\nWhat name do you want to give to the analysis?\nYour input: ")
    else:
        input_name = NameInputExcel

    print("\nRunning calculation '{}'.".format(input_name))

    df = pd.read_excel(os.path.join(FolderModelInput, '{}.xlsx'.format(NameInputExcel)))
    # CRS must be in EPSG:4326
    crs_ = 4326

    if 'shapefile_for_OSM' in df.columns:
        # When the user chooses to download a graph from OSM, they can only do the alternative distance analysis
        # download the graph from OSM with the data from the user and calculate the shortest paths
        path_shp = os.path.join(RootFolder, 'GIS/input/', '{}.shp'.format(df.iloc[0]['shapefile_for_OSM']))
        network_type = df.iloc[0]['network_type'].lower()
        road_types = df.iloc[0]['road_types']

        if 'input_data' in df.columns:
            if "path to hazard data (multiple separated by comma)" in list(df['input_data']):
                hazard_data = {'path': [os.path.join(RootFolder, 'GIS/input/', x) for x in df.loc[df['input_data'] == "path to hazard data (multiple separated by comma)", 'file_names'].iloc[0].split(",")],
                               'attribute_name': [x for x in df.loc[df['input_data'] == "attribute name(s) of hazard data (name of shapefile attribute or name that you want to give)", 'file_names'].iloc[0].split(",")],
                               'aggregation': df.loc[df['input_data'] == 'aggregation method', 'file_names'].iloc[0],
                               'threshold': df.loc[df['input_data'] == 'threshold value', 'file_names'].iloc[0]}

        if network_type in ['drive', 'drive_service', 'all', 'all_private']:
            # only drivable roads have a choice between road types
            road_types = road_types.lower().replace(',', '|')  # OSMNX takes the '|' sign as 'and' operator

        G = get_graph_from_polygon(path_shp, network_type, road_types)

        if 'Single-link Disruption' in list(df['links_analysis']):
            single_link_alternative_routes_graph(input_name, FolderModelOutput, G, crs_)
        elif 'Multi-link Disruption (1): Calculate the disruption for all damaged roads' in list(df['links_analysis']):
            multi_link_alternative_routes_graph(input_name, FolderModelOutput, G, crs_, hazard_data)
        elif "Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix" in list(
                df.links_analysis):
            input_data_dict = create_input_data_dict(df, RootFolder)
            multi_link_od_matrix_graph(input_name, FolderModelOutput, input_data_dict, hazard_data, G, crs_)
        else:
            print("You can only do a Single-link Disruption or Multi-link Disruption (1) analysis with OSM data. Run again and check your input.")

    elif 'clip_polygon_europe' in list(df['input_data']):
        # When the user chooses to use an existing graph (from OSM)
        # Save the paths and choices of the user in a dict
        input_dict = {'incl_nuts': list(df['nuts_3_regions_to_include']),
                      'incl_countries': list(df['country_codes_to_include']),
                      'clip_shp_path': df[df['input_data'] == 'clip_polygon_europe'].iloc[0]['path_to_data'],
                      'floods_path': df[df['input_data'] == 'flood_data_europe'].iloc[0]['path_to_data'],
                      'osm_path': df[df['input_data'] == 'osm_data_europe'].iloc[0]['path_to_data'],
                      'pbf_europe_path': df[df['input_data'] == 'pbf_europe'].iloc[0]['path_to_data'],
                      'nuts_3_regions': df[df['input_data'] == 'nuts_3_regions'].iloc[0]['path_to_data']}

        G = create_graph_europe(RootFolder, FolderModelOutput, input_name, input_dict, crs_)

        if 'Single-link Disruption' in list(df['links_analysis']):
            # Do the single link analysis with the chosen NUTS-3 regions
            single_link_europe(G, FolderModelOutput, input_name, crs_)
        elif 'Multi-link Disruption (1): Calculate the disruption for all damaged roads' in list(df['links_analysis']):
            # Do the multilink analysis with the flood Area of Influence data for Europe
            # multi_link_flood_all(G)
            print("Not yet implemented")
        elif 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix' in list(df['links_analysis']):
            # Do the Origin Destination matrix calculation. Need to define the origin and destination still?
            multi_link_od_matrix(G, FolderModelOutput, input_dict, 'AoI_rp100', 'val_rp100', 0, crs_)
        else:
            print("Something went wrong.. Run again and check your input.")

    else:
        # Create the input for the analyses - paths to files
        input_data_dict = create_input_data_dict(df, RootFolder)

        snapping_ = False
        snapping_threshold = 0
        pruning_ = False
        pruning_threshold = 0
        hazard_data = {}

        if "data_manipulation" in df.columns:
            if "Snapping" in list(df['data_manipulation']):
                snapping_ = True
                snapping_threshold = df.loc[df['data_manipulation'] == "Snapping", 'thresholds'].iloc[0]

            if "Pruning" in list(df['data_manipulation']):
                pruning_ = True
                pruning_threshold = df.loc[df['data_manipulation'] == "Pruning", 'thresholds']
        if "path to hazard data (multiple separated by comma)" in list(df['input_data']):
            hazard_data['path'] = [os.path.join(RootFolder, 'GIS/input/', x) for x in
                          df.loc[df['input_data'] == "path to hazard data (multiple separated by comma)", 'file_names'].iloc[0].split(",")]
            hazard_data['attribute_name'] = [x for x in df.loc[df['input_data'] == "attribute name(s) of hazard data (name of shapefile attribute or name that you want to give)", 'file_names'].iloc[0].split(",")]
            # for the following items it is variable if they are included in the input excel
            for item in ["aggregation method", "ID name to join with", "threshold value"]:
                if item in list(df['input_data']):
                    hazard_data[item.split(" ")[0]] = df.loc[df['input_data'] == item, 'file_names'].iloc[0]

        # Now, there are 4 types of analyses: alternative routes or access routes
        # combines with single or multiple link. In addition you can add a hazard map
        # to determine the area of roads that do not function anymore.
        if "Alternative Route Finder" in list(df.analysis):
            if "Single-link Disruption" in list(df.links_analysis):
                single_link_alternative_routes(input_name, FolderModelOutput, input_data_dict, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            elif "Multi-link Disruption (1): Calculate the disruption for all damaged roads" in list(df.links_analysis):
                multi_link_alternative_routes(input_name, FolderModelOutput, input_data_dict, hazard_data, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            elif "Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix" in list(df.links_analysis):
                multi_link_od_matrix(input_name, FolderModelOutput, input_data_dict, hazard_data, crs_,
                                               snapping_, snapping_threshold, pruning_, pruning_threshold)

            else:
                "Something went wrong.. Run again and check your input."

        elif "Accessibility to Key Points of Interest" in list(df.analysis):

            if "Single-link Disruption" in list(df.links_analysis):
                single_link_access_routes()

            elif "Multi-link Disruption" in list(df.links_analysis):
                multi_link_access_routes()


def create_input_data_dict(data, root_folder):
    input_data_dict = {}
    for input_ in data.input_data:
        if input_ == input_:  # check if the input is not empty (nan)
            the_value = data[data['input_data'] == input_].iloc[0]['file_names']
            if the_value == the_value:  # check if the value is not Nan
                if input_ == 'name of ID column':
                    input_data_dict['id_name'] = the_value
                    continue
                if input_ == 'ID name of both origin and destination files':
                    input_data_dict['id_od'] = the_value
                    continue
                key_name1 = '{}_path'.format(input_.replace(' ', '_').lower())
                if isinstance(the_value, str):
                    if ',' in the_value:
                        v_list = []
                        for v in the_value.split(','):
                            if input_ in ['Shapefiles for Analysis', 'Shapefiles for Diversion',
                                          'origin shapefiles', 'destination shapefiles']:
                                v_list.append(os.path.join(root_folder, 'GIS/input/', '{}.shp'.format(v)))
                            elif input_ == 'road usage data':
                                v_list.append(os.path.join(root_folder, 'model_input/', '{}.xlsx'.format(v)))
                            if input_ == 'origin shapefiles':
                                input_data_dict['o_names'] = [x.split('_')[0] for x in the_value.split(',')]
                            if input_ == 'destination shapefiles':
                                input_data_dict['d_names'] = [x.split('_')[0] for x in the_value.split(',')]
                        input_data_dict[key_name1] = v_list
                    else:
                        if input_ in ['Shapefiles for Analysis', 'Shapefiles for Diversion',
                                      'origin shapefiles', 'destination shapefiles']:
                            input_data_dict[key_name1] = os.path.join(root_folder, 'GIS/input/',
                                                                      '{}.shp'.format(the_value))
                        elif input_ == 'road usage data':
                            input_data_dict[key_name1] = os.path.join(root_folder, 'model_input/',
                                                                      '{}.xlsx'.format(the_value))
                        if input_ == 'origin shapefiles':
                            input_data_dict['o_names'] = the_value.split('_')[0]
                        if input_ == 'destination shapefiles':
                            input_data_dict['d_names'] = the_value.split('_')[0]
    return input_data_dict


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
    gdf = criticality_single_link(G, id_name, roadUsageData=road_usage_data, aadtNames=aadt_names)
    logging.info("Function [criticality_single_link]: executing")

    # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
    # todo: input here this option

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [single_link_alternative_routes]: {}".format(timer(startstart, end)))


def single_link_alternative_routes_graph(name, AllOutput, graph, crs):
    """
    This is the function to analyse roads with a single link disruption calculating
    an alternative route. The input is a graph that is downloaded from OSM.
    """
    logging.info("----------------------------- {} -----------------------------".format(name))
    print("\nExecuting analysis..")

    startstart = time.time()

    # save the graph as a shapefile
    graph_to_shp(graph, os.path.join(AllOutput, '{}_edges.shp'.format(name)),
                    os.path.join(AllOutput, '{}_nodes.shp'.format(name)))

    # CALCULATE CRITICALITY
    gdf = criticality_single_link_osm(graph)  # TODO: input the type of roads to analyse
    logging.info("Function [criticality_single_link]: executing for {}".format(name))

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [single_link_alternative_routes]: {}".format(timer(startstart,end)))


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
        G = hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # CALCULATE CRITICALITY
    gdf = criticality_multi_link_hazard(G, HazardDataDict['attribute_name'], HazardDataDict['threshold'])
    logging.info("Function [criticality_single_link]: executing")

    # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
    # todo: input here this option

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_alternative_routes]: {}".format(timer(startstart, end)))


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
    graph = hazard_intersect_graph(graph, HazardDataDict['path'], HazardDataDict['attribute_name'],
                                      name, agg=HazardDataDict['aggregation'])

    # CALCULATE CRITICALITY
    gdf = criticality_multi_link_hazard(graph, HazardDataDict['attribute_name'], HazardDataDict['threshold'], id_name)

    # save to shapefile
    gdf.crs = {'init': 'epsg:{}'.format(crs)}
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_alternative_routes_graph]: {}".format(timer(startstart, end)))


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
        G = hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # Add the origin/destination nodes to the network
    ods = read_OD_files(InputDataDict['origin_shapefiles_path'], InputDataDict['o_names'],
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

    ods = create_OD_pairs(ods, G, id_name)
    G = add_od_nodes(G, ods, id_name, name=name, file_output=AllOutput, save_shp=True)

    if weighing == 'time':
        # not yet possible for input with shapefiles, except when a max speed attribute is attached to the shapefile
        # calculate the time it takes per road segment
        avg_speeds = calc_avg_speed(G, 'highway', save_csv=True, save_path=os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        avg_speeds = pd.read_csv(os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        if len(avg_speeds.loc[avg_speeds['avg_speed'] == 0]) > 0:
            logging.info("An average speed of 50 is used in locations where the maximum speed limit is 0 in OSM data.")
            avg_speeds.loc[avg_speeds['avg_speed'] == 0, 'avg_speed'] = 50  # this is assumed
        G = assign_avg_speed(G, avg_speeds, 'highway')

        # make a time value of seconds, length of road streches is in meters
        for u, v, k, edata in G.edges.data(keys=True):
            hours = (edata['length'] / 1000) / edata['avgspeed']
            G[u][v][k][weighing] = hours * 3600

    # Calculate the preferred routes
    pref_routes = preferred_routes_od(G, weighing, id_name, ods, crs, HazardDataDict, shortest_route=True, save_shp=True, save_pickle=False,
                                         file_output=AllOutput, name=name)

    # Calculate the criticality
    gdf = criticality_multi_link_hazard_OD(G, pref_routes, weighing, HazardDataDict['attribute_name'][0],
                                              HazardDataDict['threshold'], crs)

    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_od_matrix]: {}".format(timer(startstart, end)))


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
    G = add_missing_geoms_graph(G)

    if (id_name_hazard is None) & (len(HazardDataDict) != 0):
        G = hazard_intersect_graph(G, HazardDataDict['path'], HazardDataDict['attribute_name'], name,
                                      agg=HazardDataDict['aggregation'])

    # Add the origin/destination nodes to the network
    ods = read_OD_files(InputDataDict['origin_shapefiles_path'], InputDataDict['o_names'],
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

    ods = create_OD_pairs(ods, G, id_name)
    G = add_od_nodes(G, ods, id_name, name=name, file_output=AllOutput, save_shp=True)

    if weighing == 'time':
        # calculate the time it takes per road segment
        avg_speeds = calc_avg_speed(G, 'highway', save_csv=True, save_path=os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        avg_speeds = pd.read_csv(os.path.join(AllOutput, 'avg_speeds_{}.csv'.format(name)))
        if len(avg_speeds.loc[avg_speeds['avg_speed'] == 0]) > 0:
            logging.info("An average speed of 50 is used in locations where the maximum speed limit is 0 in OSM data.")
            avg_speeds.loc[avg_speeds['avg_speed'] == 0, 'avg_speed'] = 50  # this is assumed
        G = assign_avg_speed(G, avg_speeds, 'highway')

        # make a time value of seconds, length of road streches is in meters
        for u, v, k, edata in G.edges.data(keys=True):
            hours = (edata['length'] / 1000) / edata['avgspeed']
            G[u][v][k][weighing] = hours * 3600

    # Calculate the preferred routes
    pref_routes = preferred_routes_od(G, weighing, id_name, ods, crs, HazardDataDict, shortest_route=True, save_shp=True, save_pickle=False,
                                         file_output=AllOutput, name=name)

    # Calculate the criticality
    gdf = criticality_multi_link_hazard_OD(G, pref_routes, weighing, HazardDataDict['attribute_name'][0],
                                              HazardDataDict['threshold'], crs)

    # save graph
    save_name = os.path.join(AllOutput, '{}_criticality.shp'.format(name))
    gdf_to_shp(gdf, save_name)

    print("\nThe shapefile with calculated criticality can be found here:\n{}".format(save_name))

    end = time.time()
    logging.info("Full analysis [multi_link_od_matrix_graph]: {}".format(timer(startstart, end)))


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
    lines = read_merge_shp(shapefileAnalyse=shapefile_analyse,
                              shapefileDiversion=shapefile_diversion,
                              idName=id_name,
                              crs_=crs)
    logging.info("Function [read_merge_shp]: executed with {} {}".format(shapefile_analyse, shapefile_diversion))

    # Multilinestring to linestring
    # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
    # The list of fid's is reduced by the fid's that are not anymore in the merged lines
    edges, lines_merged = merge_lines_shpfiles(lines, id_name, aadt_names, crs)
    logging.info("Function [merge_lines_shpfiles]: executed with properties {}".format(list(edges.columns)))

    if snapping:
        edges = snap_endpoints_lines(edges, SnappingThreshold, id_name, tolerance=1e-7)
        logging.info("Function [snap_endpoints_lines]: executed with threshold = {}".format(SnappingThreshold))
        # TODO: when lines are added the properties cannot be saved well - this should be integrated

    # TODO
    #    if pruning:
    #        lines = prune_lines(lines, prune_threshold=PruningThreshold)

    # merge merged lines if there are any merged lines
    if not lines_merged.empty:
        # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
        lines_merged.to_file(os.path.join(AllOutput, "{}_lines_that_merged.shp".format(name)))
        logging.info(
            "Function [edges_to_shp]: saved at {}".format(os.path.join(AllOutput, "{}_lines_that_merged".format(name))))

    # Get the unique points at the end of lines and at intersections to create nodes
    nodes = create_nodes(edges, crs)
    logging.info("Function [create_nodes]: executed")

    if snapping:
        # merged lines may be updated when new nodes are created which makes a line cut in two
        edges = cut_lines(edges, nodes, id_name, tolerance=1e-4)
        nodes = create_nodes(edges, crs)
        logging.info("Function [cut_lines]: executed")

    # save the merged lines (correct edges) as shapefile
    edges.to_file(os.path.join(AllOutput, '{}_edges.shp'.format(name)))
    logging.info("Function [edges_to_shp]: executed for '{}_edges'".format(name))

    # save the intersection points as shapefile
    nodes.to_file(os.path.join(AllOutput, '{}_nodes.shp'.format(name)))
    logging.info("Function [nodes_to_shp]: executed for '{}_nodes'".format(name))

    if id_name_hazard is not None:
        # there is hazard data available
        edges = hazard_join_id_shp(edges, HazardDataDict)

    # create tuples from the adjecent nodes and add as column in geodataframe
    resulting_network = join_nodes_edges(nodes, edges, id_name)
    logging.info("Function [join_nodes_edges]: executed")

    # save geodataframe to shapefile
    resulting_network.crs = {'init': 'epsg:{}'.format(crs)}  # set the right CRS
    resulting_network.to_file(os.path.join(AllOutput, '{}_resulting_network.shp'.format(name)))

    # Create networkx graph from geodataframe
    G = graph_from_gdf(resulting_network, nodes)
    logging.info("Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(name))

    return G


