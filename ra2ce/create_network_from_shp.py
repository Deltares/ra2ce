# -*- coding: utf-8 -*-
"""
Created on 30-9-2020

@authors:
Frederique de Groen (frederique.degroen@deltares.nl)
"""

# external modules
import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)

import networkx as nx
import osmnx
import pandas as pd
import warnings
import geopandas as gpd
import itertools
import logging
import rtree
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge
from prettytable import PrettyTable
from statistics import mean
from numpy import object as np_object
from geopy import distance

# local modules
from utils import load_config

LOG_FILENAME = os.path.join(folder, './logs/log_create_network_from_shapefile.log')
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

AllOutput = load_config()["paths"]["output"]


def create_network_from_shapefile(InputDict, crs):
    """Creates a (graph) network from a shapefile
    Args:
        name (string): name of the analysis given by user (will be part of the name of the output files)
        AllOutput (string): path to the folder where the output should be saved
        InputDict (dict): dictionairy with paths/input that is used to create the network
        crs (int): the EPSG number of the coordinate reference system that is used
        snapping (bool): True if snapping is required, False if not
        SnappingThreshold (int/float): threshold to reach another vertice to connect the edge to
        pruning (bool): True if pruning is required, False if not
        PruningThreshold (int/float): edges smaller than this length (threshold) are removed
    Returns:
        G (networkX graph): The resulting network graph
    """
    # initiate variables
    shapefile_diversion = []

    # load the input files if they are there
    if 'shp_input_data' in InputDict:
        shapefile_analyse = InputDict['shp_input_data']

    if 'shp_for_diversion' in InputDict:
        shapefile_diversion = InputDict['shp_for_diversion']

    # TODO adjust to the right names of the RA2CE tool
    # if 'infra_usage' in InputDict:
    #     road_usage_data = pd.read_excel(InputDict['infra_usage'])
    #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
    #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
    # else:
    #     aadt_names = None
    #     road_usage_data = pd.DataFrame()
    road_usage_data = pd.DataFrame()  # can be removed if the above is fixed
    aadt_names = None  # can be removed if the above is fixed

    # Load shapefile
    lines = read_merge_shp(shapefileAnalyse=shapefile_analyse,
                           shapefileDiversion=shapefile_diversion,
                           idName=InputDict['shp_unique_ID'],
                           crs_=crs)
    logging.info("Function [read_merge_shp]: executed with {} {}".format(shapefile_analyse, shapefile_diversion))

    # Multilinestring to linestring
    # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
    # The list of fid's is reduced by the fid's that are not anymore in the merged lines
    edges, lines_merged = merge_lines_shpfiles(lines, InputDict['shp_unique_ID'], aadt_names, crs)
    logging.info("Function [merge_lines_shpfiles]: executed with properties {}".format(list(edges.columns)))

    edges, id_name = gdf_check_create_unique_ids(edges, InputDict['shp_unique_ID'])

    if 'data_manipulation' in InputDict:
        if InputDict['data_manipulation'] == 'snapping':
            edges = snap_endpoints_lines(edges, InputDict['snapping_threshold'], id_name, tolerance=1e-7)
            logging.info("Function [snap_endpoints_lines]: executed with threshold = {}".format(InputDict['snapping_threshold']))

    # TODO
    #    if pruning:
    #        lines = prune_lines(lines, prune_threshold=PruningThreshold)

    # merge merged lines if there are any merged lines
    if not lines_merged.empty:
        # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
        lines_merged.to_file(os.path.join(AllOutput, "{}_lines_that_merged.shp".format(InputDict['analysis_name'])))
        logging.info(
            "Function [edges_to_shp]: saved at {}".format(
                os.path.join(AllOutput, "{}_lines_that_merged".format(InputDict['analysis_name']))))

    # Get the unique points at the end of lines and at intersections to create nodes
    nodes = create_nodes(edges, crs)
    logging.info("Function [create_nodes]: executed")

    if 'data_manipulation' in InputDict:
        if InputDict['data_manipulation'] == 'snapping':
            # merged lines may be updated when new nodes are created which makes a line cut in two
            edges = cut_lines(edges, nodes, id_name, tolerance=1e-4)
            nodes = create_nodes(edges, crs)
            logging.info("Function [cut_lines]: executed")

    # create tuples from the adjecent nodes and add as column in geodataframe
    resulting_network = join_nodes_edges(nodes, edges, id_name)
    logging.info("Function [join_nodes_edges]: executed")
    resulting_network.crs = {'init': 'epsg:{}'.format(crs)}  # set the right CRS

    # Save geodataframe of the resulting network to
    resulting_network.to_pickle(
        os.path.join(load_config()["paths"]["code"], '{}_gdf.pkl'.format(InputDict['analysis_name'])))
    print("Saved network to pickle in {}".format(
        os.path.join(load_config()["paths"]["code"], '{}_gdf.pkl'.format(InputDict['analysis_name']))))

    # Create networkx graph from geodataframe
    G = graph_from_gdf(resulting_network, nodes)
    logging.info(
        "Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(InputDict['analysis_name']))

    # Save graph to gpickle to use later for analysis
    nx.write_gpickle(G, os.path.join(AllOutput, '{}_graph.gpickle'.format(InputDict['analysis_name'])), protocol=4)
    print("Saved graph to pickle in {}".format(
        os.path.join(load_config()["paths"]["code"], '{}_graph.gpickle'.format(InputDict['analysis_name']))))

    # Save graph to shapefile for visual inspection
    graph_to_shp(G, os.path.join(AllOutput, '{}_edges.shp'.format(InputDict['analysis_name'])),
                 os.path.join(AllOutput, '{}_nodes.shp'.format(InputDict['analysis_name'])))

    return G, resulting_network


def read_merge_shp(shapefileAnalyse, shapefileDiversion, idName, crs_):
    """Imports shapefile(s) and saves attributes in a pandas dataframe.

    Args:
        shapefileAnalyse (string or list of strings): absolute path(s) to the shapefile(s) that will be used for analysis
        shapefileDiversion (string or list of strings): absolute path(s) to the shapefile(s) that will be used to calculate alternative routes but is not analysed
        idName (string): the name of the Unique ID column
        crs_ (int): the EPSG number of the coordinate reference system that is used
    Returns:
        lines (list of shapely LineStrings): full list of linestrings
        properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
    """

    # convert shapefile names to a list if it was not already a list
    if isinstance(shapefileAnalyse, str) and shapefileAnalyse != 0:
        shapefileAnalyse = [shapefileAnalyse]
    if isinstance(shapefileDiversion, str) and shapefileDiversion != 0:
        shapefileDiversion = [shapefileDiversion]

    shapefileAnalyse = [os.path.join(load_config()["paths"]["test_network_shp"], x) if x.endswith('.shp') else os.path.join(load_config()["paths"]["test_network_shp"], x + '.shp') for x in shapefileAnalyse]
    shapefileDiversion = [os.path.join(load_config()["paths"]["test_network_shp"], x) if x.endswith('.shp') else os.path.join(load_config()["paths"]["test_network_shp"], x + '.shp') for x in shapefileDiversion]

    lines = []

    # read the shapefile(s) for analysis
    for shp in shapefileAnalyse:
        lines_shp = gpd.read_file(shp)
        lines_shp['to_analyse'] = 1
        lines.append(lines_shp)

    # read the shapefile(s) for only diversion
    if isinstance(shapefileDiversion, list):
        for shp2 in shapefileDiversion:
            lines_shp = gpd.read_file(shp2)
            lines_shp['to_analyse'] = 0
            lines.append(lines_shp)

    # concatenate all shapefiles into one geodataframe
    lines = pd.concat(lines)
    lines.crs = {'init': 'epsg:{}'.format(crs_)}

    # append the length of the road stretches
    lines['length'] = lines['geometry'].apply(lambda x: line_length(x))

    if lines['geometry'].apply(lambda row: isinstance(row, MultiLineString)).any():
        for line in lines.loc[lines['geometry'].apply(lambda row: isinstance(row, MultiLineString))].iterrows():
            if len(linemerge(line[1].geometry)) > 1:
                warnings.warn(
                    "Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(
                        idName, line[1][idName]))

    print('Shapefile(s) loaded with attributes: {}.'.format(list(lines.columns.values)))  # fill in parameter names

    return lines


def merge_lines_shpfiles(lines_gdf, idName, aadtNames, crs_):
    """Asks the user for input and possibly merges the LineStrings in a geodataframe (network)
    Args:
        lines_gdf (geodataframe): the network with edges that can possibly be merged
        idName (string): name of the Unique ID column in the lines_gdf
        aadtNames (list of strings): names of the columns of the AADT (average annual daily traffic)
        crs_ (int): the EPSG number of the coordinate reference system that is used
    Returns:
        lines_gdf (geodataframe): the network with edges that are (not) merged
        lines_merged (geodataframe): the lines that are merged, if lines are merged. Otherwise it returns an empty GDF
    """
    list_lines = list(lines_gdf['geometry'])

    # Multilinestring to linestring
    try:
        merged_lines = linemerge(list_lines)  # merge the lines of both shapefiles
    except NotImplementedError as e:
        Exception("Your data contains Multi-part geometries, you cannot merge lines.", e)
        return lines_gdf, gpd.GeoDataFrame()

    while True:
        try:
            merge_input = str(input(
                "\nSome of the lines can be merged. Do you want to merge these lines? Fill in 'y' to merge lines or 'n' to not merge lines.\nYour input: ")).lower()
            if merge_input == 'y':
                print("\nYou successfully chose to merge lines.")
                break  # successfully received input --> continue below
            elif merge_input == 'n':
                print("\nYou successfully chose not to merge lines.")
                return lines_gdf, gpd.GeoDataFrame()  # successfully received input
        except ValueError:
            print("\nTry again to fill in 'y' or 'n' and press enter.")
            continue

    # continue
    if len(merged_lines.geoms) < len(list_lines) and aadtNames:
        # the number of merged lines is smaller than the number of lines in the input, so lines can be merged
        while True:
            try:
                yes_to_all = str(input(
                    """You can choose which AADT properties are chosen per road segment. Type 'all' if you want to treat all the cases the same or 'single' if you want to look at each case separately.\nYour input: """)).lower()
            except ValueError:
                print("\nTry again to fill in 'all' or 'single' and press enter.")
                continue

            if yes_to_all not in ['all', 'single']:
                print("\nTry again to fill in 'all' or 'single' and press enter.")
                continue
            else:
                print("\nYou successfully chose '{}'.".format(yes_to_all))
                break  # successfully received input

        if yes_to_all == 'all':
            # ask the user if they want to take the max, min or average for all values
            while True:
                try:
                    all_type = str(input(
                        """Choose the maximum, minimum or mean for the traffic type count in each merged line. Type 'max', 'min' or 'mean'.\nYour input: """)).lower()
                except ValueError:
                    print("\nTry again to fill in 'max', 'min' or 'mean' and press enter.")
                    continue

                if all_type not in ['max', 'min', 'mean']:
                    print("\nTry again to fill in 'max', 'min' or 'mean' and press enter.")
                    continue
                else:
                    print("\nYou successfully chose '{}'.\nCalculating for all merged segments...".format(all_type))
                    break  # successfully received input
    elif len(merged_lines.geoms) < len(list_lines) and not aadtNames:
        while True:
            try:
                the_input = input(
                    "\nDo you want to merge the lines on {}? Type 'y' for yes and 'n' for no.\nYour input: ".format(
                        idName))
                if the_input == "y":
                    # merge by ID name
                    lines_gdf = lines_gdf.dissolve(by=idName, aggfunc='max')
                    lines_gdf.reset_index(inplace=True)
                    break  # successfully received input
                elif the_input == "n":
                    break  # successfully received input
            except ValueError:
                print("\nTry again to fill in the correct letter.")
    elif len(merged_lines.geoms) == len(list_lines):
        print("No lines are merged.")
        return lines_gdf, gpd.GeoDataFrame()
    else:
        # The lines have no additional properties.
        return lines_gdf, gpd.GeoDataFrame()

    # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
    # The list of fid's is reduced by the fid's that are not anymore in the merged lines
    lines_fids = list(zip(list_lines, lines_gdf[idName]))  # create tuples from the list of lines and the list of fid's
    lines_merged = gpd.GeoDataFrame(columns=[idName, 'geometry'], crs={'init': 'epsg:{}'.format(crs_)},
                                    geometry='geometry')
    merged = gpd.GeoDataFrame(columns=[idName, 'to_analyse', 'geometry'], crs={'init': 'epsg:{}'.format(crs_)},
                              geometry='geometry')

    for mline in merged_lines:
        for line, i in lines_fids:
            full_line = line
            if line.within(mline) and not line.equals(mline):
                # if the line is within the merged line but is not the same, the line is part of a merged line
                line_set_merged = [line]
                fid_set_merged = [i]

                if aadtNames:
                    aadts_set_merged = [lines_gdf[lines_gdf[idName] == i][aadtNames].iloc[0].tolist()]
                else:
                    aadts_set_merged = []

                class_set_merged = lines_gdf[lines_gdf[idName] == i]['to_analyse'].tolist()

                while not full_line.equals(mline):
                    for line2, j in lines_fids:
                        if line2.within(mline) and not line2.equals(mline) and line != line2:
                            line_set_merged.append(line2)
                            fid_set_merged.append(j)
                            if aadtNames:
                                aadts_set_merged.append(lines_gdf[lines_gdf[idName] == i][aadtNames].iloc[0].tolist())

                            class_set_merged.append(int(lines_gdf[lines_gdf[idName] == i]['to_analyse'].iloc[0]))

                            lines_fids.remove((line2,
                                               j))  # remove the lines that have been through the iteration so there are no duplicates
                    full_line = linemerge(line_set_merged)
                lines_fids.remove(
                    (line, i))  # remove the lines that have been through the iteration so there are no duplicates
                lines_merged = lines_merged.append({idName: i, 'geometry': full_line},
                                                   ignore_index=True)  # the lines in this list are the same lines that make up the merged line

                # check with the user the right traffic count for the merged lines
                if aadts_set_merged:  # check if the list is not empty
                    aadts_set_merged = [i for i in aadts_set_merged if not all(v is None for v in i)]
                    if len(aadts_set_merged) > 1 and isinstance(aadts_set_merged[0], list):
                        if yes_to_all == "all":
                            if all_type == "max":
                                aadts_set_merged = [max(sublist) for sublist in list(map(list, zip(*aadts_set_merged)))]
                            elif all_type == "min":
                                aadts_set_merged = [min(sublist) for sublist in list(map(list, zip(*aadts_set_merged)))]
                            elif all_type == "mean":
                                aadts_set_merged = [mean(sublist) for sublist in
                                                    list(map(list, zip(*aadts_set_merged)))]
                        elif yes_to_all == "single":
                            t = PrettyTable()
                            t.add_column('index', list(range(1, len(aadts_set_merged) + 1)))
                            t.add_column('AADT vehicle types', aadts_set_merged)

                            while True:
                                try:
                                    aadt_input = input(
                                        """Road segment with id's {} is merged. Choose the right values for the AADT by entering the number indicated before the list of AADT values and pressing enter.\nYou can also choose 'max', 'min' or 'mean' for all values of the merged road segment.\nThe options: \n {} \n Your input: """.format(
                                            fid_set_merged, t))
                                    if aadt_input.isdigit():
                                        aadts_set_merged = aadts_set_merged[int(aadt_input) - 1]
                                    elif aadt_input in ['max', 'min', 'mean']:
                                        first, second = aadts_set_merged
                                        if aadt_input == "max":
                                            aadts_set_merged = [max([i, j]) for i, j in list(zip(first, second))]
                                        elif aadt_input == "min":
                                            aadts_set_merged = [min([i, j]) for i, j in list(zip(first, second))]
                                        elif aadt_input == "mean":
                                            aadts_set_merged = [mean([i, j]) for i, j in list(zip(first, second))]
                                except ValueError:
                                    print(
                                        "\nTry again to fill in one of the index values or 'max', 'min' or 'mean' and press enter.")
                                    continue
                                else:
                                    print("\nYou successfully chose '{}': {}.".format(aadt_input, aadts_set_merged))
                                    break

                # check with the user the right road class for the merged lines
                if isinstance(class_set_merged, list):
                    if len(set(class_set_merged)) == 1:
                        class_set_merged = class_set_merged[0]
                    elif len(set(class_set_merged)) > 1:
                        class_input = input(
                            """Road segment with id {} is merged. Choose the right values for the road class by entering the right road class and pressing enter. The different classes: {} \n Your input: """.format(
                                fid_set_merged, class_set_merged))
                        class_set_merged = int(class_input)

                # add values to the dataframe
                this_fid = [x[0] if isinstance(x, list) else x for x in fid_set_merged][
                    0]  # take the first feature ID for the merged lines

                # initiate dict for new row in merged gdf
                properties_dict = {idName: this_fid, 'to_analyse': class_set_merged, 'geometry': mline}

                if aadtNames:
                    if isinstance(aadts_set_merged[0], list):
                        this_aadts = aadts_set_merged[0]
                    else:
                        this_aadts = aadts_set_merged

                    # update dict for new row in merged gdf
                    properties_dict.update({a: aadt_val for a, aadt_val in zip(aadtNames, this_aadts)})

                # append row to merged gdf
                merged = merged.append(properties_dict, ignore_index=True)

            elif line.equals(mline):
                # this line is not merged
                properties_dict = {idName: i,
                                   'to_analyse': lines_gdf.loc[lines_gdf[idName] == i, 'to_analyse'].iloc[0],
                                   'geometry': mline}

                if aadtNames:
                    properties_dict.update({a: aadt_val for a, aadt_val in
                                            zip(aadtNames, lines_gdf.loc[lines_gdf[idName] == i][aadtNames].iloc[0])})
                merged = merged.append(properties_dict, ignore_index=True)

    merged['length'] = merged['geometry'].apply(lambda x: line_length(x))

    return merged, lines_merged


# get the length of the lines in meters
def line_length(line):
    """Calculate length of a line in kilometers, given in geographic coordinates.
    Args:
        line: a shapely LineString object with WGS 84 coordinates
    Returns:
        Length of line in m
    """
    # check if the projection is EPSG:4326
    distance.VincentyDistance.ELLIPSOID = 'WGS-84'
    try:
        # Swap shapely (lonlat) to geopy (latlon) points
        latlon = lambda lonlat: (lonlat[1], lonlat[0])
        if isinstance(line, LineString):
            total_length = sum(distance.distance(latlon(a), latlon(b)).meters for (a, b) in pairs(line.coords))
        elif isinstance(line, MultiLineString):
            total_length = sum(
                [sum(distance.distance(latlon(a), latlon(b)).meters for (a, b) in pairs(l.coords)) for l in line])
        else:
            warnings.warn("Something went wrong while calculating the length of the road stretches.")
    except:
        warnings.warn(
            "The CRS is not EPSG:4326. Quit the analysis, reproject the layer to EPSG:4326 and try again to run the tool.")
    return round(total_length, 0)


# Iterate over a list in overlapping pairs without wrap-around.
def pairs(lst):
    """
    Args:
        lst: an iterable/list

    Returns:
        Yields a pair of consecutive elements (lst[k], lst[k+1]) of lst. Last
        call yields the last two elements.

    Example:
        lst = [4, 7, 11, 2]
        pairs(lst) yields (4, 7), (7, 11), (11, 2)

    Source:
        https://stackoverflow.com/questions/1257413/1257446#1257446
    """
    i = iter(lst)
    prev = next(i)
    for item in i:
        yield prev, item
        prev = item


def snap_endpoints_lines(lines_gdf, max_dist, idName, tolerance=1e-7):
    """Snap endpoints of lines with endpoints or vertices of other lines
    if they are at most max_dist apart. Choose the closest endpoint or vertice.

    Args:
        lines: a list of LineStrings or a MultiLineString
        max_dist: maximum distance two endpoints may be joined together

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    max_id = max(lines_gdf[idName])

    # initialize snapped lines with list of original lines
    # snapping points is a MultiPoint object of all vertices
    snapped_lines = [line for line in list(lines_gdf['geometry'])]
    snapping_dict = vertices_from_lines(snapped_lines, list(lines_gdf[idName]))

    # isolated endpoints are being snapped to the closest vertex
    isolated_endpoints = find_isolated_endpoints(list(lines_gdf[idName]), snapped_lines)

    print("Number of isolated endpoints (points that probably need to be snapped): {} ".format(len(isolated_endpoints)))
    print("Snapping lines.. Follow the progress:")
    # only snap isolated endpoints within max_dist of another vertice / endpoint
    for i, isolated_endpoint in enumerate(isolated_endpoints):
        ids, endpoint = isolated_endpoint

        # create a list of the vertices that are not the line's own vertices
        points_without_linepoints = [value for key, value in snapping_dict.items() if key != ids]

        # create list of all points to search in
        all_vertices = [p for sublist in points_without_linepoints for p in sublist]

        # create an empty spatial index object to search in
        idx = rtree.index.Index()

        # populate the spatial index
        for j, pnt in enumerate(all_vertices):
            idx.insert(j, pnt.bounds)

        # find all vertices within a radius of max_distance as possible
        # choose closest vertice and line the vertice lays on
        target = nearest_neighbor_within(all_vertices, idx, endpoint, max_dist)

        # draw a progress bar
        drawProgressBar(i / len(isolated_endpoints))

        # do nothing if the target point is further away from the endpoint than max_dist
        # or if they are at the same location
        if not target:
            continue

        # check if the line does not yet exist
        new_line = LineString([(target.x, target.y), (endpoint.x, endpoint.y)])
        if not any(new_line.equals(another_line) for another_line in snapped_lines):
            if new_line.length > 0:
                lines_gdf = lines_gdf.append({idName: max_id + 1, 'geometry': new_line, 'length': line_length(new_line),
                                              'to_analyse': 0}, ignore_index=True)
                max_id += 1

    # TODO: remove any lines that are overlapping?

    return lines_gdf


def drawProgressBar(percent, barLen=20):
    """Draws a progress bar
    https://stackoverflow.com/questions/3002085/python-to-print-out-status-bar-and-percentage
    """
    # percent float from 0 to 1.
    sys.stdout.write("\r")
    sys.stdout.write("[{:<{}}] {:.0f}%".format("=" * int(barLen * percent), barLen, percent * 100))
    sys.stdout.flush()


def find_isolated_endpoints(linesIds, lines):
    """Find endpoints of lines that don't touch another line.

    Args:
        lines: a list of LineStrings or a MultiLineString

    Returns:
        A list of line end Points that don't touch any other line of lines

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    isolated_endpoints = []
    for i, id_line in enumerate(zip(linesIds, lines)):
        ids, line = id_line
        other_lines = lines[:i] + lines[i + 1:]
        for q in [0, -1]:
            if isinstance(line, LineString):
                endpoint = Point(line.coords[q])
                if any(endpoint.touches(another_line)
                       for another_line in other_lines):
                    continue
                else:
                    isolated_endpoints.append((ids, endpoint))
            elif isinstance(line, MultiLineString):
                endpoints = [Point(l.coords[q]) for l in line]
                for endpnt in endpoints:
                    if any(endpnt.touches(another_line)
                           for another_line in other_lines):
                        continue
                    else:
                        isolated_endpoints.append((ids, endpoint))
    return isolated_endpoints


def nearest_neighbor_within(search_points, spatial_index, point, max_distance):
    """Find nearest point among others up to a maximum distance.

    Args:
        others: a dict with keys: index of line, values: list of Points or a MultiPoint
        point: a Point
        max_distance: maximum distance to search for the nearest neighbor

    Returns:
        A shapely Point if one is within max_distance, None otherwise

    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """

    # the point from where you are searching
    if isinstance(max_distance, pd.Series):
        max_distance = max_distance[0]
    geometry_buffered = point.buffer(max_distance)

    # expand bounds by max_distance in all directions
    bounds = [a + b * max_distance for a, b in zip(geometry_buffered.bounds, [-1, -1, 1, 1])]

    # get list of fids where bounding boxes intersect
    interesting_points = [int(i) for i in spatial_index.intersection(geometry_buffered.bounds)]

    if not interesting_points:
        closest_point = None
    elif len(interesting_points) == 1:
        closest_point = search_points[interesting_points[0]]
    else:
        points_list = [search_points[ip] for ip in interesting_points]
        distance_list = [(p, point.distance(p)) for p in points_list if point.distance(p) > 0]
        closest_point, closest_distance = min(distance_list, key=lambda t: t[1])

    return closest_point


def vertices_from_lines(lines, listIds):
    """Return dict of with values: unique vertices from list of LineStrings.
    keys: index of LineString in original list
    From shapely_tools:
        @author: Dirk Eilander (dirk.eilander@deltares.nl)
        Adjusted 15-10-2019: Frederique de Groen (frederique.degroen@deltares.nl)
        Build on library from https://github.com/ojdo/python-tools/blob/master/shapelytools.py
    """
    vertices_dict = {}
    for i, line in zip(listIds, lines):
        if isinstance(line, LineString):
            vertices_dict[i] = [Point(p) for p in set(list(line.coords))]
        if isinstance(line, MultiLineString):
            all_vertices = []
            for each_line in line:
                all_vertices.extend([Point(p) for p in set(list(each_line.coords))])
            vertices_dict[i] = all_vertices
    return vertices_dict


def create_nodes(merged_lines, crs_):
    """Creates shapely points on intersections and endpoints of a list of shapely lines
    Args:
        merged_lines [list of shapely LineStrings]: the edges of a graph
    Returns:
        nodes [list of shapely Points]: the nodes of a graph
    """
    list_lines = list(merged_lines['geometry'])

    # Get all endpoints of all linestrings
    endpts = [[Point(list(line.coords)[0]), Point(list(line.coords)[-1])] for line in list_lines if
              isinstance(line, LineString)]

    # flatten the resulting list to a simple list of points
    endpts = [pt for sublist in endpts for pt in sublist]

    more_endpts = [[[Point(list(ln.coords)[0]), Point(list(ln.coords)[-1])] for ln in line] for line in list_lines if
                   isinstance(line, MultiLineString)]
    more_endpts = [pt for sublist in more_endpts for pt in sublist]
    more_endpts = [pt for sublist in more_endpts for pt in sublist]
    endpts.extend(more_endpts)

    # create nodes on intersections and on lines that should be snapped
    inters = []
    for line1, line2 in itertools.combinations(list_lines, 2):
        # Make points at intersections of lines
        if line1.intersects(line2):
            inter = line1.intersection(line2)
            if "Point" == inter.type:
                inters.append(inter)
            elif "MultiPoint" == inter.type:
                inters.extend([pt for pt in inter])
            elif "MultiLineString" == inter.type:
                multiLine = [line for line in inter]
                first_coords = multiLine[0].coords[0]
                last_coords = multiLine[len(multiLine) - 1].coords[1]
                inters.append(Point(first_coords[0], first_coords[1]))
                inters.append(Point(last_coords[0], last_coords[1]))
            elif "GeometryCollection" == inter.type:
                for geom in inter:
                    if "Point" == geom.type:
                        inters.append(geom)
                    elif "MultiPoint" == geom.type:
                        inters.extend([pt for pt in geom])
                    elif "MultiLineString" == geom.type:
                        multiLine = [line for line in geom]
                        first_coords = multiLine[0].coords[0]
                        last_coords = multiLine[len(multiLine) - 1].coords[1]
                        inters.append(Point(first_coords[0], first_coords[1]))
                        inters.append(Point(last_coords[0], last_coords[1]))

    # Extend the endpoints with the intersection points that are not endpoints
    endpts.extend([pt for pt in inters if pt not in endpts])

    # Add to GeoDataFrame and delete duplicate points
    points_gdf = gpd.GeoDataFrame({'node_fid': range(len(delete_duplicates(endpts))),
                                   'geometry': delete_duplicates(endpts)},
                                  geometry='geometry', crs={'init': 'epsg:{}'.format(crs_)})

    return points_gdf


def cut_lines(lines_gdf, nodes, idName, tolerance):
    """Cuts lines at the nodes, with a certain tolerance
    Args:
        lines_gdf (geodataframe): the network with edges that should be cut
        nodes (geodataframe): points to use for cutting the edges
        idName (string): name of the Unique ID column in the lines_gdf
        tolerance: how far a point should be from the edge to cut the edge

    Returns:
        lines_gdf (geodataframe): the network with cut edges. The IDs of the new edges counting +1 on the maximum ID number
    """
    max_id = max(lines_gdf[idName])
    list_columns = list(lines_gdf.columns.values)
    for rem in ['geometry', 'length', idName]:
        list_columns.remove(rem)

    to_add = gpd.GeoDataFrame(columns=list(lines_gdf.columns.values))
    to_remove = []
    to_iterate = zip(list(lines_gdf.index.values), list(lines_gdf[idName]), list(lines_gdf['geometry']))

    for idx, i, line in to_iterate:
        if isinstance(line, LineString):
            points_to_cut = [pnt for pnt in list(nodes['geometry']) if
                             (line.distance(pnt) < tolerance) & (line.boundary.distance(pnt) > tolerance)]
        elif isinstance(line, MultiLineString):
            points_to_cut = []
            for ln in line:
                points_to_cut.extend([pnt for pnt in list(nodes['geometry']) if
                                      (ln.distance(pnt) < tolerance) & (ln.boundary.distance(pnt) > tolerance)])

        if points_to_cut:
            # cut lines
            newlines = split_line_with_points(line=line, points=points_to_cut)
            for j, newline in enumerate(newlines):
                if j == 0:
                    # copy and remove the row of the original linestring
                    properties_dict = lines_gdf.loc[lines_gdf[idName] == i][list_columns].to_dict(orient='records')[0]

                    # add the data with one part of the cut linestring
                    properties_dict.update({idName: i, 'geometry': newline, 'length': line_length(newline)})
                    to_add = to_add.append(properties_dict, ignore_index=True)
                    logging.info("added line segment to {} {}".format(idName, i))
                else:
                    properties_dict = lines_gdf.loc[lines_gdf[idName] == i][list_columns].to_dict(orient='records')[0]
                    properties_dict.update({idName: max_id + 1, 'geometry': newline, 'length': line_length(newline)})
                    to_add = to_add.append(properties_dict, ignore_index=True)
                    logging.info("added line segment to {} {}".format(idName, i))
                    max_id += 1

            # remove the original linestring that has been cut
            to_remove.append(idx)

    lines_gdf.drop(to_remove, inplace=True)
    lines_gdf = lines_gdf.append(to_add, ignore_index=True)
    return lines_gdf


def split_line_with_points(line, points):
    """Splits a line string in several segments considering a list of points.
    """
    segments = []
    current_line = line

    # make a list of points and its distance to the start to sort them from small to large distance
    list_dist = [current_line.project(pnt) for pnt in points]
    list_dist.sort()

    for d in list_dist:
        # cut the line at a distance d
        seg, current_line = cut(current_line, d)
        if seg:
            segments.append(seg)
    segments.append(current_line)
    return segments


def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    # This is taken from shapely manual
    if (distance <= 0.0) | (distance >= line.length):
        return [None, LineString(line)]

    if isinstance(line, LineString):
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
            if pd == distance:
                return [
                    LineString(coords[:i + 1]),
                    LineString(coords[i:])]
            if pd > distance:
                cp = line.interpolate(distance)
                # check if the LineString contains an Z-value, if so, remove
                # only use XY because otherwise the snapping functionality doesn't work
                return [LineString([xy[0:2] for xy in coords[:i]] + [(cp.x, cp.y)]),
                        LineString([(cp.x, cp.y)] + [xy[0:2] for xy in coords[i:]])]
    elif isinstance(line, MultiLineString):
        for ln in line:
            coords = list(ln.coords)
            for i, p in enumerate(coords):
                pd = ln.project(Point(p))
                if pd == distance:
                    return [
                        LineString(coords[:i + 1]),
                        LineString(coords[i:])]
                if pd > distance:
                    cp = ln.interpolate(distance)
                    # check if the LineString contains an Z-value, if so, remove
                    # only use XY because otherwise the snapping functionality doesn't work
                    return [LineString([xy[0:2] for xy in coords[:i]] + [(cp.x, cp.y)]),
                            LineString([(cp.x, cp.y)] + [xy[0:2] for xy in coords[i:]])]


# def prune_lines(lines, prune_threshold):
#
#    # create nodes on intersections and on lines that should be snapped
#    inters = []
#    for line1,line2 in itertools.combinations(lines, 2):
#        # Make points at intersections of lines
#        if line1.intersects(line2):
#            inter = line1.intersection(line2)
#            if "Point" == inter.type:
#                segments1 = split_line_with_points(line1, [inter])
#                segments2 = split_line_with_points(line2, [inter])
#
#
#            elif "MultiPoint" == inter.type:
#                inters.extend([pt for pt in inter])
#            elif "MultiLineString" == inter.type:
#                multiLine = [line for line in inter]
#                first_coords = multiLine[0].coords[0]
#                last_coords = multiLine[len(multiLine)-1].coords[1]
#                inters.append(Point(first_coords[0], first_coords[1]))
#                inters.append(Point(last_coords[0], last_coords[1]))
#            elif "GeometryCollection" == inter.type:
#                for geom in inter:
#                    if "Point" == geom.type:
#                        inters.append(geom)
#                    elif "MultiPoint" == geom.type:
#                        inters.extend([pt for pt in geom])
#                    elif "MultiLineString" == geom.type:
#                        multiLine = [line for line in geom]
#                        first_coords = multiLine[0].coords[0]
#                        last_coords = multiLine[len(multiLine)-1].coords[1]
#                        inters.append(Point(first_coords[0], first_coords[1]))
#                        inters.append(Point(last_coords[0], last_coords[1]))
#    # prune lines
#    if pruning:
#        # from m to km
#        prune_threshold = prune_threshold / 1000
#
#        # remove the segments shorter than prune_threshold meter
#        new_lines = [line for line in new_lines if line.length > prune_threshold]


def join_nodes_edges(gdf_nodes, gdf_edges, idName):
    """Creates tuples from the adjecent nodes and add as column in geodataframe.
    Args:
        gdf_nodes [geodataframe]: geodataframe of the nodes of a graph
        gdf_edges [geodataframe]: geodataframe of the nodes of a graph
    Returns:
        result [geodataframe]: geodataframe of adjecent nodes from edges
    """
    # list of the edges that are not topographically correct
    incorrect_edges = []

    # add node attributes to edges
    gdf = gpd.sjoin(gdf_edges, gdf_nodes, how="left", op='intersects')

    tuples_df = pd.DataFrame({'node_A': [], 'node_B': []})

    for edge in gdf[idName].unique():
        node_tuple = gdf.loc[gdf[idName] == edge, 'node_fid']
        if len(node_tuple) > 2:
            # if there are more than 2 nodes intersecting the linestring, choose the ones at the endpoints
            # todo: check this section carefully!!
            incorrect_edges.append(edge)
            line_nodes = gdf.loc[gdf[idName] == edge, 'geometry'].iloc[0]
            if isinstance(line_nodes, LineString):
                point_coords = [Point(line_nodes.coords[0]), Point(
                    line_nodes.coords[-1])]  # these are the two endpoints of the linestring - we take these as nodes
                n = gdf_nodes[gdf_nodes['node_fid'].isin(node_tuple)]  # get the geometries of the nodes
                special_tuple = ()
                for point in list(n.geometry):
                    if any(p.equals(point) for p in point_coords):
                        special_tuple = special_tuple + (n.loc[n.geometry == point, 'node_fid'].iloc[
                                                             0],)  # find the node id of the two endpoints of the linestring
                warnings.warn(
                    "More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(
                        idName, edge, list(n['node_fid'])))
                try:
                    tuples_df = tuples_df.append({'node_A': special_tuple[0], 'node_B': special_tuple[1]},
                                                 ignore_index=True)
                except IndexError as e:
                    warnings.warn("Only one node can be found for edge with {} {}: {}".format(idName, edge, e))
            elif isinstance(line_nodes, MultiLineString):
                special_tuple = ()
                for ln in line_nodes:
                    point_coords = [Point(ln.coords[0]), Point(
                        ln.coords[-1])]  # these are the two endpoints of the linestring - we take these as nodes
                    n = gdf_nodes[gdf_nodes['node_fid'].isin(node_tuple)]  # get the geometries of the nodes
                    for point in list(n.geometry):
                        if any(p.equals(point) for p in point_coords):
                            special_tuple = special_tuple + (n.loc[n.geometry == point, 'node_fid'].iloc[
                                                                 0],)  # find the node id of the two endpoints of the linestring
                    warnings.warn(
                        "More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(
                            idName, edge, list(n['node_fid'])))
                try:
                    tuples_df = tuples_df.append({'node_A': special_tuple[0], 'node_B': special_tuple[1]},
                                                 ignore_index=True)
                except IndexError as e:
                    warnings.warn("Only one node can be found for edge with {} {}: {}".format(idName, edge, e))
        elif len(node_tuple) < 2:
            # somehow the geopandas sjoin did not find any nodes on this edge, but there are so look for them
            node_a = [i for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry) if xy.almost_equals(
                Point(list(gdf_edges.loc[gdf_edges[idName] == edge].iloc[0].geometry.coords)[0]))]
            node_b = [i for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry) if xy.almost_equals(
                Point(list(gdf_edges.loc[gdf_edges[idName] == edge].iloc[0].geometry.coords)[-1]))]
            tuples_df = tuples_df.append(
                {'node_A': gdf_nodes.loc[gdf_nodes['node_fid'] == node_a[0], 'node_fid'].iloc[0],
                 'node_B': gdf_nodes.loc[gdf_nodes['node_fid'] == node_b[0], 'node_fid'].iloc[0]}, ignore_index=True)
        elif len(node_tuple) == 2:
            # this is what you want for a good network
            tuples_df = tuples_df.append({'node_A': node_tuple.iloc[0], 'node_B': node_tuple.iloc[1]},
                                         ignore_index=True)
        else:
            warnings.warn("Something went wrong..")

    if incorrect_edges:
        warnings.warn('More than 2 nodes intersecting edges {}'.format(incorrect_edges))

    # reset indices in case they are not unique
    gdf_edges.reset_index(inplace=True, drop=True)
    tuples_df.reset_index(inplace=True, drop=True)

    result = gpd.GeoDataFrame(pd.concat([gdf_edges, tuples_df], axis=1))

    # drop all columns without values
    if result.columns[result.isnull().all()].any():
        to_drop = result.columns[result.isnull().all()]
        result.drop(to_drop, axis=1, inplace=True)

    return result


def graph_from_gdf(gdf, gdf_nodes, name='network'):
    # create a Graph object
    G = nx.MultiGraph(crs=gdf.crs)

    # create nodes on the Graph
    for index, row in gdf_nodes.iterrows():
        c = {'ID': row.node_fid, 'geometry': row.geometry}
        G.add_node(row.node_fid, **c)

    # create edges on top of the nodes
    for index, row in gdf.iterrows():
        dict_row = row.to_dict()
        G.add_edge(u_for_edge=dict_row['node_A'], v_for_edge=dict_row['node_B'], **dict_row)

    # make a name
    G.graph['name'] = name

    return G


def hazard_join_id_shp(roads, HazardDataDict):
    # read and join hazard data
    col_id, col_val = HazardDataDict['ID'], HazardDataDict['attribute_name'][0]

    # Fiona is not always loading the geodataframe with all data, so try a few times to get it correct
    attempts = 0
    while attempts < 3:
        try:
            hazard = gpd.read_file(HazardDataDict['path'][0])
            hazard = hazard[[col_id, col_val]]
            break
        except KeyError:
            attempts += 1
            print("Attempt {} to load hazard data: {}".format(attempts, HazardDataDict['path'][0].split('\\')[-1]))

    for i in range(1, len(HazardDataDict['path'])):
        attempts = 0
        while attempts < 3:
            try:
                hazard2 = gpd.read_file(HazardDataDict['path'][i], encoding="utf-8")
                hazard = pd.concat([hazard, hazard2[[col_id, col_val]]], ignore_index=True)
                break
            except KeyError:
                attempts += 1
                print("Attempt {} to load hazard data: {}".format(attempts, HazardDataDict['path'][i].split('\\')[-1]))

    if (col_val in roads) and (col_id in roads):
        hazard = pd.concat([hazard, roads[[col_id, col_val]]], ignore_index=True)

    # Not necessary now
    # hazard.drop_duplicates(inplace=True)

    for ii in hazard[col_id].unique():
        roads.loc[roads[col_id] == ii, "_{}".format(col_val)] = max(hazard.loc[(hazard[col_id] == ii), col_val])

    return roads


# Delete duplicate points
def delete_duplicates(all_points):
    points = [point for point in all_points]
    uniquepoints = []
    for point in points:
        if not any(p.almost_equals(point) for p in uniquepoints):
            uniquepoints.append(point)
    return uniquepoints


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
    nodes, edges = osmnx.graph_to_gdfs(G, node_geometry=False)

    dfs = [edges, nodes]
    for df in dfs:
        for col in df.columns:
            if df[col].dtype == np_object and col != df.geometry.name:
                df[col] = df[col].astype(str)

    print('\nSaving nodes as shapefile: {}'.format(node_shp))
    print('\nSaving edges as shapefile: {}'.format(edge_shp))

    nodes.to_file(node_shp, driver='ESRI Shapefile', encoding='utf-8')
    edges.to_file(edge_shp, driver='ESRI Shapefile', encoding='utf-8')


def gdf_check_create_unique_ids(gdf, idName):
    # Check if the ID's are unique per edge: if not, add an own ID called 'fid'
    if len(gdf[idName].unique()) < len(gdf.index):
        new_id_name = 'fid'
        gdf[new_id_name] = list(range(gdf.index))
        print(
            "Added a new unique identifier field {} because the original field '{}' did not contain unique values per road segment.".format(
                new_id_name, idName))
        return gdf, new_id_name
    else:
        return gdf, idName


def graph_check_create_unique_ids(graph, idName):
    # Check if the ID's are unique per edge: if not, add an own ID called 'fid'
    if len(set([str(e[-1][idName]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
        new_id_name = 'fid'
        i = 0
        for u, v, k in graph.edges(keys=True):
            graph[u][v][k][new_id_name] = i
            i += 1
        print(
            "Added a new unique identifier field {} because the original field '{}' did not contain unique values per road segment.".format(
                new_id_name, idName))
        return graph, new_id_name
    else:
        return graph, idName


if __name__ == '__main__':
    # General test input
    input_crs = 4326  # the Coordinate Reference System of the input shapefiles should be in EPSG:4326 because OSM always uses this CRS

    # Test specific test input
    input_InputDict = {0: {'analysis_name': 'test1',
                      'analysis': 'Redundancy-based criticality',
                      'links_analysis': 'Single-link Disruption',
                      'network_source': 'Network based on shapefile',
                      'shp_input_data': 'part_of_DR_roads',
                      'shp_unique_ID': 'fid'}}

    graph, gdf = create_network_from_shapefile(InputDict=input_InputDict, crs=input_crs)

    print("Ran create_graph_shp.py successfully!")
