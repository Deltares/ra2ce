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


### FROM COMMON.PY FROM COACCH - START ###
def timer(start,end):
   hours, rem = divmod(end-start, 3600)
   minutes, seconds = divmod(rem, 60)
   return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)


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


def graph_from_osm(osm_files, multidirectional=False):
    """
    Takes in a list of osmnx compatible files as strings, creates individual graph from each file then combines all
    graphs using the compose_all function from networkx. Most suited for cases where each file represents part of the
    same greater network.

    Arguments:
        list_of_osm_files [list or str]: list of osm filenames as strings, see osmnx documentation for compatible file
        formats
        multidirectional [bool]: if True, function returns a directional graph, if false, function returns an
        undirected graph

    Returns:
        G []: A networkx ... or ... instance

    From Kees van Ginkel
    """
    sys.setrecursionlimit(10**5)

    graph_list = []

    if isinstance(osm_files, str):
        G = osmnx.graph_from_file(osm_files, simplify=True)
    else:
        for osm_file in osm_files:
            graph_list.append(osmnx.graph_from_file(osm_file, simplify=True))

        G = nx.compose_all(graph_list)

    if not multidirectional:
        G = G.to_undirected()

    return G


def poly_files_europe(output_path, area_shp):
    # create the name of the output file
    name_output = area_shp.split("\\")[-1].split(".")[0]

    # TODO: write a function that if there is an area with small islands or other complicated shapes that the
    # algorithm cannot handle, that it makes a convex hull. Don't know if this is the best option but the
    # best option for now.

    NUTS_poly = gpd.read_file(area_shp)
    print("Current CRS:", NUTS_poly.crs['init'])
    if NUTS_poly.crs['init'] != 'epsg:4326':
        print("Changing CRS to EPSG:4326")
        NUTS_poly = NUTS_poly.to_crs(epsg=4326)  # Change into the WGS84 = EPSG4326 coordinate system of OSM.

    # start writing the .poly file (overwrites if the file exists)
    f = open(output_path, 'w')
    f.write(name_output + "\n")

    try:
        i = 0
        # write the coordinates of the ring to the .poly file
        polygon = NUTS_poly.geometry.exterior[0]

        f.write(str(i) + "\n")

        for geom in polygon.coords:
            f.write("    " + str(geom[0]) + "     " + str(geom[1]) + "\n")

        # close the ring of one subpolygon if done
        f.write("END" + "\n")

    except AttributeError as e:
        print("No poly file for {} was created: {}".format(name_output, e))

    # close the file when done
    f.write("END" + "\n")
    f.close()

    print("Poly file saved to: {}".format(output_path))


def clip_osm(osm_convert_path, planet_path, area_poly, area_o5m):
    """ Clip the an area osm file from the larger continent (or planet) file and save to a new osm.pbf file.
    This is much faster compared to clipping the osm.pbf file while extracting through ogr2ogr.

    This function uses the osmconvert tool, which can be found at http://wiki.openstreetmap.org/wiki/Osmconvert.

    Either add the directory where this executable is located to your environmental variables or just put it in the 'scripts' directory.

    Arguments:
        osm_convert_path: path string to the palce where the osm_convert executable is located
        planet_path: path string to the .planet files containing the OSM Europe or OSM world file from which you want to crop
        area_poly: path string to the .poly file, made through the 'create_poly_files' function.
        area_o5m: path string indicating the final output dir and output name of the new .o5m file.

    Returns:
        a clipped and filtered .o5m file (saved as area_o5m .o5m)

    Script from Kees van Ginkel, adjusted by Frederique de Groen
    """
    print('{} started!'.format(area_o5m))

    try:
        if os.path.exists(area_o5m) is not True:
            command = '""{}"  "{}" -B="{}" --complete-ways -o="{}""'.format(osm_convert_path, planet_path, area_poly, area_o5m)
            print(command)
            os.system(command)
        print('{} finished!'.format(area_o5m))

    except:
        print('{} did not finish!'.format(area_o5m))


def filter_osm(osm_filter_path, area_o5m, filtered_area_o5m):
    """Filters an o5m OSM file to only motorways, trunks, primary and secondary roads
    """
    print('{} started!'.format(filtered_area_o5m))

    try:
        if os.path.exists(filtered_area_o5m) is not True:
            command = '""{}"  "{}" --keep="highway=motorway =motorway_link =primary =primary_link =secondary =secondary_link =trunk =trunk_link" > "{}""'.format(osm_filter_path, area_o5m, filtered_area_o5m)
            print(command)
            os.system(command)
        print('{} finished!'.format(filtered_area_o5m))

    except:
        print('{} did not finish!'.format(filtered_area_o5m))


def import_flood_data(floods_path, incl_country, crs, incl_nuts=[], excl_nuts=[], save_shp=False, shp_path=""):
    """
    Imports the flood data from Kees' model and outputs as a merged geodataframe.
    There is the option to save the data to a shapefile

    Arguments:
        data_path [string]: absolute path to pickles with flood data per NUTS-3 region
        incl_country [list or string]: list or string of country code(s) to include (e.g. Austria=AT)
        excl_nuts [list of strings]: list of NUTS-3 codes to exclude
        save_shp [bool]: True for saving the shapefile in path shp_path
        shp_path [string]: the path and name of the shapefile to save to

    Returns:
        gdf_all [geopandas dataframe]: geodataframe of all pickles
    """

    # input variables
    try:
        if isinstance(incl_country, str):
            list_filenames = [filename for filename in os.listdir(floods_path) if (filename.endswith("segment_raw.pkl")) &
                              (((filename.split('_')[0][:2] == incl_country) & (filename.split('_')[0] not in excl_nuts)) |
                    (filename.split('_')[0] in incl_nuts))]
        elif isinstance(incl_country, list):
            list_filenames = [filename for filename in os.listdir(floods_path) if (filename.endswith("segment_raw.pkl")) &
                              (((filename.split('_')[0][:2] in incl_country) & (filename.split('_')[0] not in excl_nuts)) |
                        (filename.split('_')[0] in incl_nuts))]
        elif incl_country is None:
            # incl_country is None:
            list_filenames = [filename for filename in os.listdir(floods_path) if (filename.endswith("segment_raw.pkl")) &
                        (filename.split('_')[0] in incl_nuts)]
    except ReferenceError as e:
        warnings.warn("You have not filled in the arguments of import_flood_data correctly: {}".format(e))

    print(list_filenames)
    list_columns_to_keep = ['infra_type', 'geometry', 'lanes', 'bridge', 'length',
           'road_type', 'NUTS-3', 'NUTS-2', 'NUTS-1', 'NUTS-0', 'AoI_rp100', 'val_rp100']

    # Merge all pickles into one geodataframe
    # First make a dataframe from the first pickle
    df_all = pd.read_pickle(os.path.join(floods_path, list_filenames[0]))[list_columns_to_keep]
    df_all['uid'] = df_all['NUTS-3'] + '_' + df_all.index
    df_all.reset_index(inplace=True)

    # then add all the other pickles
    for i in list_filenames[1:]:
        df_next = pd.read_pickle(os.path.join(floods_path, i))[list_columns_to_keep]
        df_next['uid'] = df_next['NUTS-3'] + '_' + df_next.index
        df_next.reset_index(inplace=True)
        df_all = df_all.append(df_next, ignore_index=True)

    gdf_all = gpd.GeoDataFrame(df_all, crs=crs, geometry='geometry')

    # Save as shapefile
    if save_shp:
        gdf_all.to_file(shp_path)

    return gdf_all


def df_to_shp(df, crs, file_path):
    """
    Saves a dataframe with a geometry column to a shapefile. Here use for saving
    the results of an analysis to a shapefile.

    Arguments:
        df [DataFrame]: dataframe with a geometry column
        crs [string]: the CRS EPSG (e.g. 4326)
        file_path [string]: the full path to where the shapefile must be saved.
            Ends with '.shp'
    """

    # clean up file before writing
    df = df[~df['geometry'].isnull()]

    for col in df.columns:
        if df[col].dtype == np_object and col != df.geometry.name:
            df[col] = df[col].astype(str)

    gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs=crs)
    gdf.to_file(file_path)


def match_ids(G, flood_data, value_column, group_column, aadt_path=None, dict_eroads=None):
    """
    Merges the flood data with the graph, via the OSM id's. If road segments are
    merged in the process of creating the graph with osmnx, then all floods are
    added to the graph.

    Arguments:
        G [networkx graph]: networkx graph with at least osmid
        flood_data [geodataframe]: geodataframe with all the flood data from Kees' model
        value_column [string]: the name of the column name of for example the inundation depth per AoI
        group_column [string]: the name of the column name of for example AoI number

    Returns:
        G [networkx graph]: networkx graph with the osm id of the chosen segment,
        inundation depth and area of interest added
    """
    if isinstance(aadt_path, str):
        # import the AADT data as df
        aadt = pd.read_excel(aadt_path)

    for u, v, k, edata in G.edges(data=True, keys=True):
        values_dict = {'match_id': [0], value_column: [0], group_column: [0], 'NUTS-3': [0]}

        if isinstance(edata['osmid'], list):
            floods_all = flood_data[flood_data['osm_id'].isin(edata['osmid'])]
            if not floods_all.empty:
                # all floods are saved in the graph
                if len(set(floods_all[group_column])) > 1:
                    # there are multiple floods on the same road segment
                    floods = floods_all[[group_column, value_column, 'NUTS-3']].groupby(
                        ['AoI_rp100', 'NUTS-3']).agg('max').reset_index()
                    values_dict[value_column] = list(floods[value_column])
                    values_dict[group_column] = list(floods[group_column])
                    values_dict['NUTS-3'] = list(floods['NUTS-3'])

                    list_osmids = []
                    for val, gr, nut in zip(list(floods[value_column]), list(floods[group_column]),
                                            list(floods['NUTS-3'])):
                        list_osmids.append(
                            floods_all.loc[(floods_all[group_column] == gr) & (floods_all[value_column] == val) &
                                           (floods_all['NUTS-3'] == nut), 'osm_id'].iloc[0])

                    if list_osmids:
                        values_dict['match_id'] = list_osmids[0]  # just add the first osm id
                else:
                    # there is only one AoI intersecting with the road segment
                    v1, v2, v3, v4 = \
                        floods_all.loc[(floods_all[value_column] == max(floods_all[value_column]))].iloc[0][
                        ['osm_id', value_column, group_column, 'NUTS-3']]
                    if isinstance(v1, list):
                        v1 = v1[0]
                    values_dict['match_id'] = v1
                    values_dict[value_column] = [v2]
                    values_dict[group_column] = [v3]
                    values_dict['NUTS-3'] = [v4]
            else:
                # if there has not been a flood but there are multiple osm id's, append the first id
                values_dict['match_id'] = edata['osmid'][0]
                if not flood_data[flood_data['osm_id'] == edata['osmid'][0]][['NUTS-3']].empty:
                    values_dict['NUTS-3'] = [flood_data[flood_data['osm_id'] == edata['osmid'][0]][['NUTS-3']]]

            # if dict_eroads:
            #     # check if any of the merged roads is an e-road
            #     e_road = [dict_eroads[id_] for id_ in edata['osmid'] if id_ in dict_eroads]
            #     if e_road:
            #         e_road = e_road[0]
            #     else:
            #         e_road = np.nan
        else:
            # if dict_eroads:
            #     # check if the road is an e-classified road, otherwise append NaN
            #     if edata['osmid'] in dict_eroads:
            #         e_road = dict_eroads[edata['osmid']]
            #     else:
            #         e_road = np.nan

            values_dict['match_id'] = edata['osmid']
            if not flood_data[flood_data['osm_id'] == edata['osmid']]['NUTS-3'].empty:
                values_dict['NUTS-3'] = [flood_data[flood_data['osm_id'] == edata['osmid']].iloc[0]['NUTS-3']]
            if not flood_data[flood_data['osm_id'] == edata['osmid']][value_column].empty:
                values_dict[value_column] = [flood_data[flood_data['osm_id'] == edata['osmid']].iloc[0][value_column]]
            if not flood_data[flood_data['osm_id'] == edata['osmid']][[group_column]].empty:
                values_dict[group_column] = [flood_data[flood_data['osm_id'] == edata['osmid']].iloc[0][group_column]]

        # change the variable 'oneway' from boolean to int to enable saving the graph as a shapefile
        oneway = 0
        if edata['oneway']:
            oneway = 1

        # indicator if the segment should be analysed or not
        analyse = 1
        if 'bridge' in edata:
            if edata['bridge'] == 'yes':
                analyse = 0

        # add the AADT values
        # if isinstance(aadt_path, str):
        #     if not isinstance(e_road, float):
        #         if ';' in e_road:
        #             e_roads = e_road.split(';')
        #             for r in e_roads:
        #                 if r in aadt.e_road.values:
        #                     aadt_tot = aadt[aadt['e_road'] == r].total_vehicles.iloc[0]
        #                     aadt_a = aadt[aadt['e_road'] == r].category_a.iloc[0]
        #                     aadt_b = aadt[aadt['e_road'] == r].category_b.iloc[0]
        #                     aadt_c = aadt[aadt['e_road'] == r].category_c.iloc[0]
        #                     aadt_d = aadt[aadt['e_road'] == r].category_d.iloc[0]
        #         elif isinstance(e_road, str):
        #             if e_road in aadt.e_road.values:
        #                 aadt_tot = aadt[aadt['e_road'] == e_road].total_vehicles.iloc[0]
        #                 aadt_a = aadt[aadt['e_road'] == e_road].category_a.iloc[0]
        #                 aadt_b = aadt[aadt['e_road'] == e_road].category_b.iloc[0]
        #                 aadt_c = aadt[aadt['e_road'] == e_road].category_c.iloc[0]
        #                 aadt_d = aadt[aadt['e_road'] == e_road].category_d.iloc[0]
        #     else:
        #         aadt_tot = np.nan
        #         aadt_a = np.nan
        #         aadt_b = np.nan
        #         aadt_c = np.nan
        #         aadt_d = np.nan

        # remove the name column
        edata.pop('name', None)

        # append the matching id, flood depth and area of interest to the edge
        if isinstance(aadt_path, str):
            attrs = {(u, v, k): {'match_id': values_dict['match_id'],
                     value_column: values_dict[value_column],
                     group_column: values_dict[group_column],
                     'oneway': oneway,
                     'analyse': analyse,
                     'NUTS-3': values_dict['NUTS-3'],
                     # 'E-road': e_road,
                     'aadt_tot': aadt_tot,
                     'aadt_a': aadt_a,
                     'aadt_b': aadt_b,
                     'aadt_c': aadt_c,
                     'aadt_d': aadt_d}}
        else:
            attrs = {(u, v, k): {'match_id': values_dict['match_id'],
                     value_column: values_dict[value_column],
                     group_column: values_dict[group_column],
                     'oneway': oneway,
                     'analyse': analyse,
                     'NUTS-3': values_dict['NUTS-3'],
                     # 'E-road': e_road
                                 }}
        nx.set_edge_attributes(G, attrs)

    return G


def sort_group_edges(graph, group, sort, min_sort):
    """
    The function group the edges per group and then sorts those groups on the input sort.
    The threshold that are defined (hardcoded) in the function are that the inundation
    should be higher than 'min_sort' and the edge should have a column 'for_analys' that should
    have the value 1 to be taken into account for the analysis.

    Arguments:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        group [string] = the attribute of the edges in the graph that you want to group by
        sort [string] = the attribute of the edges in the graph that you want to sort by (in reverse order)
        min_sort [int/float] = the minimum which is taken into account to remove edges

    Returns:
        to_remove [list] : a list of the grouping variable with the filtered and sorted edges that
        belong to that group
    """
    if isinstance(graph, list):
        edgelist = graph
    else:
        edgelist = [e for e in graph.edges.data()]

    # remove segments with no flood, flood lower than min_sort, bridge segments and later also the segments that should not be analysed
    filtered_list = [x for x in edgelist if (x[-1][sort] > min_sort) & (x[-1]['analyse'] == 1)]

    # sort the dictionaries on the Area of Interest: highest flood first
    area_of_interest = sorted(filtered_list, key= lambda x: 0 if str(x[-1][group]) == 'nan' else x[-1][group], reverse=True)

    # take only the dictionary of each edge in the edgelist and remove the edges without an Area of Interest
    area_of_interest = [x for x in area_of_interest if str(x[-1][group]) != 'nan']

    # create a list of the edges grouped by area of interest
    to_remove = []

    for k, v in itertools.groupby(area_of_interest, key= lambda x: x[-1][group]):
        to_remove.append([k, list(v)])

    # sort the edges within the area of interest groups on inundation depth from high to low
    to_remove = [[edge_in_AoI[0], sorted(edge_in_AoI[1], key= lambda x: 0 if str(x[-1][sort]) == 'nan' else x[-1][sort], reverse=True)] for edge_in_AoI in to_remove]

    return to_remove


def OSM_dict_from_other_tags(other_tags):
    """
    @author: Elco Koks
    Edited by Kees jan 2019
    Edited by Frederique de Groen sept 2019

    Creates a dict from the other_tags string of an OSM road segment

    Arguments:
    *other_tags* (string) : string containing all the other_tags data from the OSM road segment

    Returns:
    *lanes* (int) : integer containing the number of lines of the road segment
    """

    dct = {}
    if other_tags is not None:
        try:
            lst = other_tags.split("\",\"")
            for i in lst:
                j = i.split('=>')
                dct['{}'.format(j[0].replace("\"",""))] =j[1].replace("\"","")
        except:
            print("Dict construction did not work for: {}".format(other_tags))
    return dct


def fetch_e_roads_data(osm_data, regions, country):
    """
    @author: Elco Koks
    Edited by Kees jan 2019
    Edited by Frederique de Groen sept 2019 from fetch_roads to fetch_e_roads_data

    Function to extract all roads from OpenStreetMap for the specified region.

    Arguments:
        *osm_data* (string) -- string of data path where the OSM extracts are located.

        *region* (list of strings) -- list of NUTS3 code of regions to consider.

    Returns:
        *dictionary* -- dictionary of {osm_id:e-road, etc.} in the specified **regions**.

    """
    import ogr

    # DICT TO SAVE DATA
    dict_roads = {}

    list_filenames = [filename for filename in os.listdir(osm_data) if (filename.endswith(".osm.pbf")) & ((filename.split('_')[0] in regions) | (country == filename.split('_')[0][:2]))]

    for region in list_filenames:
        ## LOAD FILE
        osm_path = os.path.join(osm_data, region)
        driver = ogr.GetDriverByName('OSM')
        data = driver.Open(osm_path)

        ## PERFORM SQL QUERY
        try:
            sql_lyr = data.ExecuteSQL("SELECT osm_id,highway,other_tags FROM lines WHERE highway IS NOT NULL")

            ## EXTRACT ROADS
            for feature in sql_lyr:
                if feature.GetField('highway') is not None:
                    osm_id = feature.GetField('osm_id')
                    shapely_geo = loads(feature.geometry().ExportToWkt())
                    if shapely_geo is None:
                        continue
                    try:
                        other_tags = feature.GetField('other_tags')
                        dct = OSM_dict_from_other_tags(other_tags)  # convert the other_tags string to a dict

                        if 'int_ref' in dct:  # other metadata can be drawn similarly
                            try:
                                int_ref = dct['int_ref']
                            except:
                                print("\nConverting to integer did not work for region: {} OSM ID: {} with other tags: {}".format(region, osm_id, other_tags))
                        else:
                            int_ref = np.NaN

                    except Exception as e:
                        print("\nException occured when reading metadata from 'other_tags', region: {}  OSM ID: {}, Exception = {}\n".format(region, osm_id, e))
                        int_ref = np.NaN

                    ## SAVE IN DICT
                    if int_ref == int_ref:
                        dict_roads[int(osm_id)] = int_ref  # include other_tags to see all available metata

        except:
            print("No highway data found for {}".format(region))
            continue

    return dict_roads


def multi_link_all(graph, grouping, sorting, min_sort):
    """
    The function removes all links in a group (grouping) and that have a minimum value
    of min_sort for the variable sorting (that is sorted from high to low). For each
    link it calculates the alternative path, af any available.

    Args:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        grouping [string] = the attribute of the edges in the graph that you want to group by
        sorting [string] = the attribute of the edges in the graph that you want to sort by (in reverse order)
        min_sort [int/float] = the minimum which is taken into account to remove edges

    Returns:
        df [pandas DataFrame] = a pandas DataFrame with all graph information and the
            calculated alternative distances
    """
    # Create a geodataframe from the full graph
    gdf = osmnx.graph_to_gdfs(graph, nodes=False)

    # Create the edgelist that consist of edges that should be removed
    edges_remove = sort_group_edges(graph, group=grouping, sort=sorting, min_sort=min_sort)

    # dataframe for saving the calculations of the alternative routes
    df_calculated = pd.DataFrame(columns=['u', 'v', 'alt_dist', 'alt_nodes'])

    for AoI in edges_remove:
        # Make a copy of the graph
        G = graph.copy()

        # remove the edges per flood event (Area of Influence)
        to_remove = AoI[-1]
        list_remove = [(x[0],x[1]) for x in to_remove if x[-1]['analyse'] == 1]
        G.remove_edges_from(list_remove)

        for u,v in list_remove:
            # check if the nodes are still connected
            if nx.has_path(G, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(G, u, v, weight='length')

                # save alternative route nodes
                alt_nodes = nx.dijkstra_path(G, u, v, weight='length')

                # append to calculation dataframe
                df_calculated = df_calculated.append({'u':u, 'v':v, 'alt_dist':alt_dist, 'alt_nodes':alt_nodes}, ignore_index=True)
            else:
                # append to calculation dataframe
                df_calculated = df_calculated.append({'u':u, 'v':v, 'alt_dist':np.NaN, 'alt_nodes':np.NaN}, ignore_index=True)

    # Merge the dataframes
    gdf = gdf.merge(df_calculated, how='left', on=['u', 'v'])

    # calculate the difference in distance
    gdf['diff_dist'] = [dist - length if dist == dist else np.NaN for (dist,length) in zip(gdf['alt_dist'],gdf['length'])]

    return gdf


def multi_link_one(graph, grouping, sorting, min_sort, first_n, save_path, crs):
    """
    The function removes all links in a group (grouping) and that have a minimum value
    of min_sort for the variable sorting (that is sorted from high to low). For each
    link it calculates the alternative path, af any available. This function only
    removes one group at the time and saves the data from removing that group.

    Arguments:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        grouping [string] = the attribute of the edges in the graph that you want to group by
        sorting [string] = the attribute of the edges in the graph that you want to sort by (in reverse order)
        min_sort [int/float] = the minimum which is taken into account to remove edges
        first_n [int] = the first n of the groups which is sorted by
        save_path [string] = path and name where and how you want to save the shapefile
            shapefile is saved with a number appended from 0 to first_n
            the 0 is the shapefile with the largest flood
    """
    # Create the edgelist that consist of edges that should be removed
    edges_remove = sort_group_edges(graph, group=grouping, sort=sorting, min_sort=min_sort)

    # Only look at the first n groups
    edges_remove = edges_remove[0:first_n]

    for i, AoI in enumerate(edges_remove):
        # dataframe for saving the calculations of the alternative routes
        df_calculated = pd.DataFrame(columns=['u', 'v', 'alt_dist', 'alt_nodes'])

        # Make a copy of the graph
        G = graph.copy()

        # Create a geodataframe from the full graph
        gdf = osmnx.graph_to_gdfs(G, nodes=False)

        # remove the edges per flood event (Area of Influence)
        to_remove = AoI[-1]
        list_remove = [(x[0],x[1]) for x in to_remove if x[-1]['analyse'] == 1]
        G.remove_edges_from(list_remove)

        for u,v in list_remove:
            # check if the nodes are still connected
            if nx.has_path(G, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(G, u, v, weight='length')

                # save alternative route nodes
                alt_nodes = nx.dijkstra_path(G, u, v)

                # append to calculation dataframe
                df_calculated = df_calculated.append({'u':u, 'v':v, 'alt_dist':alt_dist, 'alt_nodes':alt_nodes}, ignore_index=True)
            else:
                # append to calculation dataframe
                df_calculated = df_calculated.append({'u':u, 'v':v, 'alt_dist':np.NaN, 'alt_nodes':np.NaN}, ignore_index=True)

        # Merge the dataframes
        gdf = gdf.merge(df_calculated, how='left', on=['u', 'v'])

        # calculate the difference in distance
        gdf['diff_dist'] = [dist - length if dist == dist else np.NaN for (dist,length) in zip(gdf['alt_dist'],gdf['length'])]

        # add the AoI that is analysed to the geodataframe
        gdf['AoI_anlysd'] = AoI[0]

        df_to_shp(df=gdf, crs=crs, file_path=r"{}{}.shp".format(save_path, i))
### FROM COMMON.PY FROM COACCH - END ###


def read_merge_shp(shapefileAnalyse, shapefileDiversion, idName, crs_):
    """Imports shapefile(s) and saves attributes in a pandas dataframe.

    Parameters:
        shapefileAnalyse (string or list of strings): absolute path(s) to the shapefile(s) that will be used for analysis
        shapefileDiversion (string or list of strings): absolute path(s) to the shapefile(s) that will be used to calculate alternative routes but is not analysed
    Returns:
        lines (list of shapely LineStrings): full list of linestrings
        properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
    """

    # convert shapefile names to a list if it was not already a list
    if isinstance(shapefileAnalyse, str) and shapefileAnalyse != 0:
        shapefileAnalyse = [shapefileAnalyse]
    if isinstance(shapefileDiversion, str) and shapefileDiversion != 0:
        shapefileDiversion = [shapefileDiversion]

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
                warnings.warn("Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(idName, line[1][idName]))

    print('Shapefile(s) loaded with attributes: {}.'.format(list(lines.columns.values)))  # fill in parameter names

    return lines


def merge_lines_shpfiles(lines_gdf, idName, aadtNames, crs_):
    list_lines = list(lines_gdf['geometry'])

    # Multilinestring to linestring
    merged_lines = linemerge(list_lines)  # merge the lines of both shapefiles

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

    if merge_input == 'y':
        if len(merged_lines.geoms) < len(list_lines) and aadtNames:
            # the number of merged lines is smaller than the number of lines in the input, so lines can be merged
            while True:
                try:
                    yes_to_all = str(input("""You can choose which AADT properties are chosen per road segment. Type 'all' if you want to treat all the cases the same or 'single' if you want to look at each case separately.\nYour input: """)).lower()
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
                        all_type = str(input("""Choose the maximum, minimum or mean for the traffic type count in each merged line. Type 'max', 'min' or 'mean'.\nYour input: """)).lower()
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
                    the_input = input("\nDo you want to merge the lines on {}? Type 'y' for yes and 'n' for no.\nYour input: ".format(idName))
                    if the_input == "y":
                        # TODO
                        print("This function is not implemented yet.")
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

                            lines_fids.remove((line2, j))  # remove the lines that have been through the iteration so there are no duplicates
                    full_line = linemerge(line_set_merged)
                lines_fids.remove((line, i))  # remove the lines that have been through the iteration so there are no duplicates
                lines_merged = lines_merged.append({idName: i, 'geometry': full_line}, ignore_index=True)  # the lines in this list are the same lines that make up the merged line

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
                                aadts_set_merged = [mean(sublist) for sublist in list(map(list, zip(*aadts_set_merged)))]
                        elif yes_to_all == "single":
                            t = PrettyTable()
                            t.add_column('index', list(range(1, len(aadts_set_merged)+1)))
                            t.add_column('AADT vehicle types', aadts_set_merged)

                            while True:
                                try:
                                    aadt_input = input("""Road segment with id's {} is merged. Choose the right values for the AADT by entering the number indicated before the list of AADT values and pressing enter.\nYou can also choose 'max', 'min' or 'mean' for all values of the merged road segment.\nThe options: \n {} \n Your input: """.format(fid_set_merged, t))
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
                                    print("\nTry again to fill in one of the index values or 'max', 'min' or 'mean' and press enter.")
                                    continue
                                else:
                                    print("\nYou successfully chose '{}': {}.".format(aadt_input, aadts_set_merged))
                                    break
                else:
                    aadts_set_merged = [None] * len(aadtNames)

                # check with the user the right road class for the merged lines
                if isinstance(class_set_merged, list):
                    if len(set(class_set_merged)) == 1:
                        class_set_merged = class_set_merged[0]
                    elif len(set(class_set_merged)) > 1:
                        class_input = input("""Road segment with id {} is merged. Choose the right values for the road class by entering the right road class and pressing enter. The different classes: {} \n Your input: """.format(fid_set_merged, class_set_merged))
                        class_set_merged = int(class_input)

                # add values to the dataframe
                this_fid = [x[0] if isinstance(x, list) else x for x in fid_set_merged][0]  # take the first feature ID for the merged lines
                if isinstance(aadts_set_merged[0], list):
                    this_aadts = aadts_set_merged[0]
                else:
                    this_aadts = aadts_set_merged

                if aadtNames:
                    properties_dict = {idName: this_fid, 'to_analyse': class_set_merged, 'geometry': mline}
                    properties_dict.update({a: aadt_val for a, aadt_val in zip(aadtNames, this_aadts)})
                    merged = merged.append(properties_dict, ignore_index=True)

            elif line.equals(mline):
                # this line is not merged
                if aadtNames:
                    properties_dict = {idName: i, 'to_analyse': lines_gdf.loc[lines_gdf[idName] == i, 'to_analyse'].iloc[0],
                                       'geometry': mline}
                    properties_dict.update({a: aadt_val for a, aadt_val in zip(aadtNames, lines_gdf.loc[lines_gdf[idName] == i][aadtNames].iloc[0])})
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
            total_length = sum([sum(distance.distance(latlon(a), latlon(b)).meters for (a, b) in pairs(l.coords)) for l in line])
        else:
            warnings.warn("Something went wrong while calculating the length of the road stretches.")
    except:
        warnings.warn("The CRS is not EPSG:4326. Quit the analysis, reproject the layer to EPSG:4326 and try again to run the tool.")
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


# Delete duplicate points
def delete_duplicates(all_points):
    points = [point for point in all_points]
    uniquepoints = []
    for point in points:
        if not any(p.almost_equals(point) for p in uniquepoints):
            uniquepoints.append(point)
    return uniquepoints

# TODO: Check the connectivity of the shapefile


def create_nodes(merged_lines, crs_):
    """Creates shapely points on intersections and endpoints of a list of shapely lines
    Args:
        merged_lines [list of shapely LineStrings]: the edges of a graph
    Returns:
        nodes [list of shapely Points]: the nodes of a graph
    """
    list_lines = list(merged_lines['geometry'])

    # Get all endpoints of all linestrings
    endpts = [[Point(list(line.coords)[0]), Point(list(line.coords)[-1])] for line in list_lines if isinstance(line, LineString)]

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
                last_coords = multiLine[len(multiLine)-1].coords[1]
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
                        last_coords = multiLine[len(multiLine)-1].coords[1]
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
            points_to_cut = [pnt for pnt in list(nodes['geometry']) if (line.distance(pnt) < tolerance) & (line.boundary.distance(pnt) > tolerance)]
        elif isinstance(line, MultiLineString):
            points_to_cut = []
            for ln in line:
                points_to_cut.extend([pnt for pnt in list(nodes['geometry']) if (ln.distance(pnt) < tolerance) & (ln.boundary.distance(pnt) > tolerance)])

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
                    properties_dict.update({idName: max_id+1, 'geometry': newline, 'length': line_length(newline)})
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
                    LineString(coords[:i+1]),
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
                        LineString(coords[:i+1]),
                        LineString(coords[i:])]
                if pd > distance:
                    cp = ln.interpolate(distance)
                    # check if the LineString contains an Z-value, if so, remove
                    # only use XY because otherwise the snapping functionality doesn't work
                    return [LineString([xy[0:2] for xy in coords[:i]] + [(cp.x, cp.y)]),
                            LineString([(cp.x, cp.y)] + [xy[0:2] for xy in coords[i:]])]


#def prune_lines(lines, prune_threshold):
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
            # todo: check this section!!
            incorrect_edges.append(edge)
            line_nodes = gdf.loc[gdf[idName] == edge, 'geometry'].iloc[0]
            if isinstance(line_nodes, LineString):
                point_coords = [Point(line_nodes.coords[0]), Point(line_nodes.coords[-1])]  # these are the two endpoints of the linestring - we take these as nodes
                n = gdf_nodes[gdf_nodes['node_fid'].isin(node_tuple)]  # get the geometries of the nodes
                special_tuple = ()
                for point in list(n.geometry):
                    if any(p.equals(point) for p in point_coords):
                        special_tuple = special_tuple + (n.loc[n.geometry == point, 'node_fid'].iloc[0], )  # find the node id of the two endpoints of the linestring
                warnings.warn("More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(idName, edge, list(n['node_fid'])))
                try:
                    tuples_df = tuples_df.append({'node_A': special_tuple[0], 'node_B': special_tuple[1]}, ignore_index=True)
                except IndexError as e:
                    warnings.warn("Only one node can be found for edge with {} {}: {}".format(idName, edge, e))
            elif isinstance(line_nodes, MultiLineString):
                special_tuple = ()
                for ln in line_nodes:
                    point_coords = [Point(ln.coords[0]), Point(ln.coords[-1])]  # these are the two endpoints of the linestring - we take these as nodes
                    n = gdf_nodes[gdf_nodes['node_fid'].isin(node_tuple)]  # get the geometries of the nodes
                    for point in list(n.geometry):
                        if any(p.equals(point) for p in point_coords):
                            special_tuple = special_tuple + (n.loc[n.geometry == point, 'node_fid'].iloc[
                                                                 0],)  # find the node id of the two endpoints of the linestring
                    warnings.warn("More than two nodes are intersecting with edge {}: {}. The nodes that are intersecting are: {}".format(idName, edge, list(n['node_fid'])))
                try:
                    tuples_df = tuples_df.append({'node_A': special_tuple[0], 'node_B': special_tuple[1]},
                                             ignore_index=True)
                except IndexError as e:
                    warnings.warn("Only one node can be found for edge with {} {}: {}".format(idName, edge, e))
        elif len(node_tuple) < 2:
            # somehow the geopandas sjoin did not find any nodes on this edge, but there are so look for them
            node_a = [i for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry) if xy.almost_equals(Point(list(gdf_edges.loc[gdf_edges[idName] == edge].iloc[0].geometry.coords)[0]))]
            node_b = [i for i, xy in zip(gdf_nodes.node_fid, gdf_nodes.geometry) if xy.almost_equals(Point(list(gdf_edges.loc[gdf_edges[idName] == edge].iloc[0].geometry.coords)[-1]))]
            tuples_df = tuples_df.append({'node_A': gdf_nodes.loc[gdf_nodes['node_fid'] == node_a[0], 'node_fid'].iloc[0],
                                          'node_B': gdf_nodes.loc[gdf_nodes['node_fid'] == node_b[0], 'node_fid'].iloc[0]}, ignore_index=True)
        elif len(node_tuple) == 2:
            # this is what you want for a good network
            tuples_df = tuples_df.append({'node_A': node_tuple.iloc[0], 'node_B': node_tuple.iloc[1]}, ignore_index=True)
        else:
            warnings.warn("Something went wrong..")

    if incorrect_edges:
        warnings.warn('More than 2 nodes intersecting edges {}'.format(incorrect_edges))

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
        other_lines = lines[:i] + lines[i+1:]
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


def getKeysByValue(dictOfElements, value):
    """
    https://thispointer.com/python-how-to-find-keys-by-value-in-dictionary/
    """
    theKey = 0
    listOfItems = dictOfElements.items()
    for item in listOfItems:
        if value in item[1]:
            theKey = item[0]
    return theKey


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
    bounds = [a+b*max_distance for a, b in zip(geometry_buffered.bounds, [-1, -1, 1, 1])]

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
        drawProgressBar(i/len(isolated_endpoints))

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
    """
    https://stackoverflow.com/questions/3002085/python-to-print-out-status-bar-and-percentage
    """
    # percent float from 0 to 1.
    sys.stdout.write("\r")
    sys.stdout.write("[{:<{}}] {:.0f}%".format("=" * int(barLen * percent), barLen, percent*100))
    sys.stdout.flush()


def read_OD_files(origin_paths, origin_names, destination_paths, destination_names, od_id, crs_):
    origin = gpd.GeoDataFrame(columns=[od_id, 'o_id', 'geometry'], crs=crs_)
    destination = gpd.GeoDataFrame(columns=[od_id, 'd_id', 'geometry'], crs=crs_)

    if isinstance(origin_paths, str):
        origin_paths = [origin_paths]
    if isinstance(destination_paths, str):
        destination_paths = [destination_paths]
    if isinstance(origin_names, str):
        origin_names = [origin_names]
    if isinstance(destination_names, str):
        destination_names = [destination_names]

    for op, on in zip(origin_paths, origin_names):
        origin_new = gpd.read_file(op, crs=crs_)
        origin_new = origin_new[[od_id, 'geometry']]
        origin_new['o_id'] = on + "_" + origin_new[od_id].astype(str)
        origin = origin.append(origin_new, ignore_index=True, sort=False)

    for dp, dn in zip(destination_paths, destination_names):
        destination_new = gpd.read_file(dp, crs=crs_)
        destination_new = destination_new[[od_id, 'geometry']]
        destination_new['d_id'] = dn + "_" + destination_new[od_id].astype(str)
        destination = destination.append(destination_new, ignore_index=True, sort=False)

    od = pd.concat([origin, destination], sort=False)
    od[od_id] = list(range(len(od.index)))

    return od


def create_OD_pairs(od, graph, id_name, name=None, file_output=None, save_shp=False, save_pickle=False):
    """Get centroids of the selected NUTS-3 regions and gets closest vertice on the road of a graph.
    Args:
        origins [string]: file path of shapefile of the NUTS-3 regions in Europe
        country_codes [list of string(s)]: list of NUTS country codes
        graph [networkX graph]: graph of the roads of a or multiple European countries
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        save_pickle [bool]: True/False to save the OD pairs to a pickle in the folder 'file_output'
    Returns:
        centroids: dataframe of vertices closest to the centroids of the selected NUTS-3 regions
    """

    # find closest vertice of road network to centroid
    # create dictionary of the roads geometries
    edge_list = [e for e in graph.edges.data() if 'geometry' in e[-1]]
    vertices_dict = {}
    for line in edge_list:
        vertices_dict[(line[0], line[1])] = [Point(p) for p in set(list(line[-1]['geometry'].coords))]

    # create list of all points to search in
    all_vertices = [p for sublist in list(vertices_dict.values()) for p in sublist]

    # create an empty spatial index object to search in
    idx = rtree.index.Index()

    # populate the spatial index
    for i, pnt in enumerate(all_vertices):
        idx.insert(i, pnt.bounds)

    od = find_closest_vertice(od, idx, all_vertices, vertices_dict, edge_list, id_name)

    # save OD points
    if save_shp:
        gdf_to_shp(od, os.path.join(file_output, name+"_od_pairs.shp"))
        print("Saved OD pairs to shapefiles: {} and {}".format(os.path.join(file_output, name+"_od_pairs.shp")))
    if save_pickle:
        pickle.dump(od, open(os.path.join(file_output, name+"_od_pairs.p"), 'wb'))
        print("Saved OD pairs to pickles: {} and {}".format(os.path.join(file_output, name+"_od_pairs.p")))

    return od


def find_closest_vertice(origins_destinations, spatial_idx, search_vertices, vertices_dict, edge_list, id_name):
    ODs = []
    match_ids = []
    for i, c in enumerate(origins_destinations['geometry']):
        # find the closest vertice and line the vertice lays on
        target = list(spatial_idx.nearest(c.bounds))

        # draw a progress bar
        drawProgressBar(i / len(origins_destinations))

        # do nothing if the target point is further away from the endpoint than max_dist
        # or if they are at the same location
        if not target:
            continue

        points_list = [search_vertices[ip] for ip in target]

        # check on which road this point lays
        road_i = getKeysByValue(vertices_dict, points_list[0])
        match_ids.append([i[-1][id_name] for i in edge_list if (road_i[0] == i[0]) and (road_i[1] == i[1])][0])

        # save in list
        ODs.append(points_list[0])

    # save in dataframe
    origins_destinations['OD'] = ODs
    origins_destinations['match_ids'] = match_ids

    # save the road vertices closest to the centroids as geometry, delete the centroid geometry
    origins_destinations = gpd.GeoDataFrame(origins_destinations, geometry='OD')
    origins_destinations = origins_destinations.drop(columns=['geometry'])

    return origins_destinations


def add_od_nodes(graph, od, id_name, name=None, file_output=None, save_shp=False, save_pickle=False):
    """From a geodataframe of vertices on a graph, adds nodes on that graph.
    Args:
        graph [networkX graph]: graph of the roads of a or multiple European countries
        centroids [geodataframe]: geodataframe from the function 'create_OD_pairs'
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        save_pickle [bool]: True/False to save the OD pairs to a pickle in the folder 'file_output'
    Returns:
        graph: networkX graph with the nodes closes to the centroids of the NUTS-3 regions added.
        The ID's of the added nodes are adding in number from the highest ID of the nodes in the original graph.
    """
    # To make it easier to match the match_ids potential lists are turned into strings (or strings to strings)
    od['match_ids'] = od['match_ids'].astype(str)

    # Check the highest node id, to add on that
    max_node_id = max([n for n in graph.nodes()])

    for i in range(len(od.index)):
        # the vertice on the edge that is closest to the origin/destination point
        match_OD = od.iloc[i]['OD']

        # Check which roads belong to the centroids closest vertices
        all_matches = [e for e in graph.edges(data=True, keys=True) if str(e[-1][id_name]) == od.iloc[i]['match_ids']]
        if len(all_matches) > 1:
            all_matches = [am for am in all_matches if match_OD in [(Point(p) for p in set(list(am[-1]['geometry'].coords)))]]
        m = all_matches[0]

        if 'geometry' in m[-1]:
            match_geom = m[-1]['geometry']
            match_edge = m[:3]
            match_name = od.iloc[i]['o_id']
            if not match_name == match_name:
                # match_name is nan, the point is not an origin but a destination
                match_name = od.iloc[i]['d_id']

            new_lines = split_line_with_points(match_geom, [match_OD])
            if len(new_lines) == 2:
                line1, line2 = new_lines
            else:
                # if the vertice is at the end of the road; you don't have to add a new node
                # but do add a new attribute to the node
                if (graph.nodes[match_edge[0]]['geometry'].coords[0][1] == match_OD.coords[0][1]) & (graph.nodes[match_edge[0]]['geometry'].coords[0][0] == match_OD.coords[0][0]):
                    if 'od_id' in graph.nodes[match_edge[0]]:
                        # the node already has a origin/destination attribute
                        graph.nodes[match_edge[0]]['od_id'] = graph.nodes[match_edge[0]]['od_id'] + ',' + match_name
                    else:
                        graph.nodes[match_edge[0]]['od_id'] = match_name
                elif (graph.nodes[match_edge[1]]['geometry'].coords[0][1] == match_OD.coords[0][1]) & (graph.nodes[match_edge[1]]['geometry'].coords[0][0] == match_OD.coords[0][0]):
                    if 'od_id' in graph.nodes[match_edge[1]]:
                        graph.nodes[match_edge[1]]['od_id'] = graph.nodes[match_edge[1]]['od_id'] + ',' + match_name
                    else:
                        graph.nodes[match_edge[1]]['od_id'] = match_name
                continue

            new_node_id = max_node_id + 1
            max_node_id = new_node_id

            graph.add_node(new_node_id, y=match_OD.coords[0][1], x=match_OD.coords[0][0], geometry=match_OD, od_id=match_name)

            edge_data = graph.edges[match_edge]

            # Check which line is connected to which node. There can be 8 different combinations
            if (graph.nodes[match_edge[0]]['geometry'].coords[0][1] == line2.coords[-1][1]) & (graph.nodes[match_edge[0]]['geometry'].coords[0][0] == line2.coords[-1][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['geometry'].coords[0][1] == line2.coords[0][1]) & (graph.nodes[match_edge[1]]['geometry'].coords[0][0] == line2.coords[0][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['geometry'].coords[0][1] == line2.coords[0][1]) & (graph.nodes[match_edge[0]]['geometry'].coords[0][0] == line2.coords[0][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['geometry'].coords[0][1] == line2.coords[-1][1]) & (graph.nodes[match_edge[1]]['geometry'].coords[0][0] == line2.coords[-1][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['geometry'].coords[0][1] == line1.coords[0][1]) & (graph.nodes[match_edge[1]]['geometry'].coords[0][0] == line1.coords[0][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['geometry'].coords[0][1] == line1.coords[-1][1]) & (graph.nodes[match_edge[0]]['geometry'].coords[0][0] == line1.coords[-1][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['geometry'].coords[0][1] == line1.coords[-1][1]) & (graph.nodes[match_edge[1]]['geometry'].coords[0][0] == line1.coords[-1][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['geometry'].coords[0][1] == line1.coords[0][1]) & (graph.nodes[match_edge[0]]['geometry'].coords[0][0] == line1.coords[0][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            # remove the edge that is split in two
            u, v, k = match_edge
            graph.remove_edge(u, v, k)

    if save_shp:
        graph_to_shp(graph, os.path.join(file_output, '{}_OD_edges.shp'.format(name)),
                     os.path.join(file_output, '{}_OD_nodes.shp'.format(name)))
    if save_pickle:
        nx.write_gpickle(graph, os.path.join(file_output, '{}_graph.gpickle'.format(name)))
        print("Saved graph to pickle in {}".format(os.path.join(file_output, '{}_graph.gpickle'.format(name))))

    return graph


def preferred_routes_od(graph, weighing_name, idName, od, crs, hazard_data, shortest_route, save_shp, save_pickle, file_output, name):
    """Computes the quikest/shortest routes between Origin/Destination nodes
    Args:
        graph [networkX graph]: graph for which the preferred routes should be computed
        weighing_name [string]: name of the attribute to weigh with (e.g. length, time, etc.)
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        crs [int]: CRS EPSG, like 4326
    Returns:
        pref_routes [geodataframe]: dataframe with all O/D pairs, their preferred route and the weighing of that route
    """
    # dataframe to save the preferred routes
    pref_routes = gpd.GeoDataFrame(columns=['o_node', 'd_node', 'origin', 'destination',
                                            'pref_path', weighing_name, 'match_ids', 'geometry'],
                                   geometry='geometry', crs={'init': 'epsg:{}'.format(crs)})

    # create list of origin-destination pairs
    od_pairs = [(a, b) for a in od.loc[od['o_id'].notnull(), 'o_id'] for b in od.loc[od['d_id'].notnull(), 'd_id']]
    all_nodes = [(n, v['od_id']) for n, v in graph.nodes(data=True) if 'od_id' in v]
    od_nodes = []
    for aa, bb in od_pairs:
        # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
        od_nodes.append(([(n, n_name) for n, n_name in all_nodes if (n_name == aa) | (aa in n_name)][0],
                         [(n, n_name) for n, n_name in all_nodes if (n_name == bb) | (bb in n_name)][0]))

    # create the routes between all OD pairs
    for o, d in od_nodes:
        if nx.has_path(graph, o[0], d[0]):
            # calculate the length of the preferred route
            pref_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing_name)

            # save preferred route nodes
            pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing_name)

            # found out which edges belong to the preferred path
            edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

            pref_edges = []
            match_list = []
            for u, v in edgesinpath:
                # get edge with the lowest weighing if there are multiple edges that connect u and v
                edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing_name])[0]
                if 'geometry' in graph[u][v][edge_key]:
                    pref_edges.append(graph[u][v][edge_key]['geometry'])
                else:
                    pref_edges.append(LineString([graph.nodes[u]['geometry'], graph.nodes[v]['geometry']]))
                if idName in graph[u][v][edge_key]:
                    match_list.append(graph[u][v][edge_key][idName])

            # compile the road segments into one geometry
            pref_edges = MultiLineString(pref_edges)
            pref_routes = pref_routes.append({'o_node': o[0], 'd_node': d[0], 'origin': o[1],
                                              'destination': d[1], 'pref_path': pref_nodes,
                                              weighing_name: pref_route, 'match_ids': match_list,
                                              'geometry': pref_edges}, ignore_index=True)

    if shortest_route:
        pref_routes = pref_routes.loc[pref_routes.sort_values('length').groupby('o_node').head(3).index]

    # intersect the origin and destination nodes with the hazard map (now only geotiff possible)
    pref_routes['d_disrupt'] = None
    pref_routes['o_disrupt'] = None
    pref_routes['d_{}'.format(hazard_data['attribute_name'][0])] = None
    pref_routes['o_{}'.format(hazard_data['attribute_name'][0])] = None
    src = rasterio.open(hazard_data['path'][0])
    for i in range(len(pref_routes.index)):
        dest = graph.nodes[int(pref_routes.d_node.iloc[i])]['geometry']
        if (src.bounds.left < dest.coords[0][0] < src.bounds.right) and (
                src.bounds.bottom < dest.coords[0][1] < src.bounds.top):
            hzrd = [x.item(0) for x in src.sample(dest.coords)][0]
            pref_routes['d_{}'.format(hazard_data['attribute_name'][0])].iloc[i] = hzrd
            if hzrd > hazard_data['threshold']:
                pref_routes['d_disrupt'].iloc[i] = 'disrupted'
            else:
                pref_routes['d_disrupt'].iloc[i] = 'not disrupted'
        else:
            pref_routes['d_{}'.format(hazard_data['attribute_name'][0])].iloc[i] = 0
            pref_routes['d_disrupt'].iloc[i] = 'unknown'
        orig = graph.nodes[int(pref_routes.o_node.iloc[i])]['geometry']
        if (src.bounds.left < orig.coords[0][0] < src.bounds.right) and (
                src.bounds.bottom < orig.coords[0][1] < src.bounds.top):
            hzrd = [x.item(0) for x in src.sample(orig.coords)][0]
            pref_routes['o_{}'.format(hazard_data['attribute_name'][0])].iloc[i] = hzrd
            if hzrd > hazard_data['threshold']:
                pref_routes['o_disrupt'].iloc[i] = 'disrupted'
            else:
                pref_routes['o_disrupt'].iloc[i] = 'not disrupted'
        else:
            pref_routes['o_{}'.format(hazard_data['attribute_name'][0])].iloc[i] = 0
            pref_routes['o_disrupt'].iloc[i] = 'unknown'

    if save_shp:
        gdf_to_shp(pref_routes, os.path.join(file_output, '{}_pref_routes.shp'.format(name)))
        print("Preferred routes saved to {}".format(os.path.join(file_output, '{}_pref_routes.shp'.format(name))))

    if save_pickle:
        pref_routes[['origin', 'destination', 'AoIs', 'pref_path', weighing_name,
                     'match_ids']].to_pickle(os.path.join(file_output, '{}_pref_routes.pkl'.format(name)))
        print("Preferred routes saved to {}".format(os.path.join(file_output, '{}_pref_routes.pkl'.format(name))))

    return pref_routes


def create_OD_pairs_europe(nuts_3_shp, country_codes, graph, excl_nuts=[], incl_nuts=[], name=None, file_output=None, save_shp=False, save_pickle=False):
    """Get centroids of the selected NUTS-3 regions and gets closest vertice on the road of a graph.
    Args:
        nuts_3_shp [string]: file path of shapefile of the NUTS-3 regions in Europe
        country_codes [list of string(s)]: list of NUTS country codes
        graph [networkX graph]: graph of the roads of a or multiple European countries
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        save_pickle [bool]: True/False to save the OD pairs to a pickle in the folder 'file_output'
    Returns:
        centroids: dataframe of vertices closest to the centroids of the selected NUTS-3 regions
    """
    nuts = gpd.read_file(nuts_3_shp)

    # get only the nuts regions in the selected countries
    if len(incl_nuts) > 0:
        nuts_selection = nuts.loc[((nuts['CNTR_CODE'].isin(country_codes)) & (~nuts['NUTS_ID'].isin(excl_nuts))) |
                                  (nuts['NUTS_ID'].isin(incl_nuts))]
    else:
        nuts_selection = nuts.loc[(nuts['CNTR_CODE'].isin(country_codes)) & (~nuts['NUTS_ID'].isin(excl_nuts))]

    print(nuts_selection)
    # get centroids from NUTS-3 regions
    nuts_selection['centroid'] = nuts_selection['geometry'].centroid

    centroids = nuts_selection[['LEVL_CODE', 'NUTS_ID', 'CNTR_CODE', 'NUTS_NAME', 'FID', 'centroid']]
    centroids = gpd.GeoDataFrame(centroids, geometry='centroid')

    # reproject to 4326
    centroids.crs = {'init': 'epsg:3035'}
    centroids = centroids.to_crs({'init': 'epsg:4326'})

    # find closest vertice of road network to centroid
    # create dictionary of the roads geometries
    edge_list = [e for e in graph.edges.data() if 'geometry' in e[-1]]
    vertices_dict = {}
    for line in edge_list:
        vertices_dict[(line[0], line[1])] = [Point(p) for p in set(list(line[-1]['geometry'].coords))]

    # create list of all points to search in
    all_vertices = [p for sublist in list(vertices_dict.values()) for p in sublist]

    # create an empty spatial index object to search in
    idx = rtree.index.Index()

    # populate the spatial index
    for i, pnt in enumerate(all_vertices):
        idx.insert(i, pnt.bounds)

    ODs = []
    match_ids = []
    for i, c in enumerate(centroids.centroid):
        # find the closest vertice and line the vertice lays on
        target = list(idx.nearest(c.bounds))

        # draw a progress bar
        drawProgressBar(i / len(centroids))

        # do nothing if the target point is further away from the endpoint than max_dist
        # or if they are at the same location
        if not target:
            continue

        points_list = [all_vertices[ip] for ip in target]

        # check on which road this point lays
        road_i = getKeysByValue(vertices_dict, points_list[0])
        match_ids.append([i[-1]['match_id'] for i in edge_list if (road_i[0] == i[0]) and (road_i[1] == i[1])][0])

        # save in list
        ODs.append(points_list[0])

    # save in dataframe
    centroids['OD'] = ODs
    centroids['match_ids'] = match_ids

    # save the road vertices closest to the centroids as geometry, delete the centroid geometry
    centroids = gpd.GeoDataFrame(centroids, geometry='OD')
    centroids = centroids.drop(columns=['centroid'])
    centroids.crs = {'init': 'epsg:4326'}

    # save OD points
    if save_shp:
        gdf_to_shp(centroids, os.path.join(file_output, name+"_OD.shp"))
        print("Saved centroids of {} to shapefile: {}".format(os.path.join(file_output, name+"_OD.shp"), name))
    if save_pickle:
        pickle.dump(centroids, open(os.path.join(file_output, name+"_OD.p"), 'wb'))
        print("Saved centroids of {} to pickle: {}".format(os.path.join(file_output, name+"_OD.p"), name))

    return centroids


def add_centroid_nodes(graph, centroids, name=None, file_output=None, save_shp=False, save_pickle=False):
    """From a geodataframe of vertices on a graph, adds nodes on that graph.
    Args:
        graph [networkX graph]: graph of the roads of a or multiple European countries
        centroids [(geo)dataframe]: (geo)dataframe from the function 'create_OD_pairs'
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        save_pickle [bool]: True/False to save the OD pairs to a pickle in the folder 'file_output'
    Returns:
        graph: networkX graph with the nodes closes to the centroids of the NUTS-3 regions added.
        The ID's of the added nodes are adding in number from the highest ID of the nodes in the original graph.
    """
    # build in some robustness
    if any(isinstance(x, list) for x in centroids['match_ids'].apply(type)):
        centroids['match_ids'] = centroids['match_ids'].apply(lambda x: list(map(int, x[1:-1].split(', '))))

    # Check which roads belong to the centroids closest vertices
    matches = [e for e in graph.edges(data=True, keys=True) if e[-1]['match_id'] in list(centroids['match_ids'])]

    # Check the highest node id, to add on that
    max_node_id = max([n[0] for n in graph.nodes.data()])

    for m in matches:
        if 'geometry' in m[-1]:
            match_geom = m[-1]['geometry']
            match_edge = m[0:3]
            match_id = m[-1]['match_id']
            match_OD = centroids.loc[centroids['match_ids'] == match_id, 'OD'].iloc[0]
            match_nuts3 = centroids.loc[centroids['match_ids'] == match_id, 'NUTS_ID'].iloc[0]

            new_lines = split_line_with_points(match_geom, [match_OD])
            if len(new_lines) == 2:
                line1, line2 = new_lines
            else:
                # if the vertice is at the end of the road you don't have to add a new node
                # but do add a new attribute to the node
                if (graph.nodes[match_edge[0]]['y'] == match_OD.coords[0][1]) & (
                        graph.nodes[match_edge[0]]['x'] == match_OD.coords[0][0]):
                    graph.nodes[match_edge[0]]['nuts3'] = match_nuts3
                if (graph.nodes[match_edge[1]]['y'] == match_OD.coords[0][1]) & (
                        graph.nodes[match_edge[1]]['x'] == match_OD.coords[0][0]):
                    graph.nodes[match_edge[1]]['nuts3'] = match_nuts3
                continue

            new_node_id = max_node_id + 1
            max_node_id = new_node_id

            graph.add_node(new_node_id, y=match_OD.coords[0][1], x=match_OD.coords[0][0], osmid=np.nan, nuts3=match_nuts3)

            edge_data = graph.edges[match_edge]

            # Check which line is connected to which node. There can be 4 different combinations
            if (graph.nodes[match_edge[0]]['y'] == line2.coords[-1][1]) & (graph.nodes[match_edge[0]]['x'] == line2.coords[-1][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['y'] == line2.coords[0][1]) & (graph.nodes[match_edge[1]]['x'] == line2.coords[0][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['y'] == line2.coords[0][1]) & (graph.nodes[match_edge[0]]['x'] == line2.coords[0][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['y'] == line2.coords[-1][1]) & (graph.nodes[match_edge[1]]['x'] == line2.coords[-1][0]):
                edge_data.update(length=line_length(line2), geometry=line2)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['y'] == line1.coords[0][1]) & (graph.nodes[match_edge[1]]['x'] == line1.coords[0][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['y'] == line1.coords[-1][1]) & (graph.nodes[match_edge[0]]['x'] == line1.coords[-1][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[1]]['y'] == line1.coords[-1][1]) & (graph.nodes[match_edge[1]]['x'] == line1.coords[-1][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[1], new_node_id, match_edge[-1], **edge_data)

            if (graph.nodes[match_edge[0]]['y'] == line1.coords[0][1]) & (graph.nodes[match_edge[0]]['x'] == line1.coords[0][0]):
                edge_data.update(length=line_length(line1), geometry=line1)
                graph.add_edge(match_edge[0], new_node_id, match_edge[-1], **edge_data)

            # remove the edge that is split in two
            u, v, k = match_edge
            graph.remove_edge(u, v, k)

    if save_shp:
        graph_to_shp(graph, os.path.join(file_output, '{}_OD_edges.shp'.format(name)),
                     os.path.join(file_output, '{}_OD_nodes.shp'.format(name)))
        print("Saved graph to shapefiles: {}, {}".format(os.path.join(file_output, '{}_OD_edges.shp'.format(name)),
                                                         os.path.join(file_output, '{}_OD_nodes.shp'.format(name))))
    if save_pickle:
        nx.write_gpickle(graph, os.path.join(file_output, '{}_graph.gpickle'.format(name)))
        print("Saved graph to pickle in {}".format(os.path.join(file_output, '{}_graph.gpickle'.format(name))))

    return graph


def preferred_routes_europe(graph, weighing_name, name=None, file_output=None, save_shp=False, save_pickle=False, crs=4326):
    """Computes the quikest/shortest routes between Origin/Destination nodes
    Args:
        graph [networkX graph]: graph for which the preferred routes should be computed
        weighing_name [string]: name of the attribute to weigh with (e.g. length, time, etc.)
        name [string]: name of the analysis
        file_output [string]: path to folder where the geodataframe and/or pickle should be stored
        save_shp [bool]: True/False to save the OD pairs to a shapefile in the folder 'file_output'
        crs [int]: CRS EPSG, like 4326
    Returns:
        pref_routes [geodataframe]: dataframe with all O/D pairs, their preferred route and the weighing of that route
    """
    # dataframe to save the preferred routes
    pref_routes = gpd.GeoDataFrame(columns=['o_node', 'd_node', 'origin', 'destination', 'AoIs',
                                            'pref_path', weighing_name, 'match_ids', 'geometry'],
                                   geometry='geometry', crs={'init': 'epsg:{}'.format(crs)})

    od_nodes = [(n, v['nuts3']) for n, v in graph.nodes(data=True) if 'nuts3' in v]

    # create the routes between all OD pairs
    for o, d in itertools.combinations(od_nodes, 2):
        if nx.has_path(graph, o[0], d[0]):
            # calculate the length of the preferred route
            pref_route = nx.dijkstra_path_length(graph, o[0], d[0], weight=weighing_name)

            # save preferred route nodes
            pref_nodes = nx.dijkstra_path(graph, o[0], d[0], weight=weighing_name)

            # found out which edges belong to the preferred path
            edgesinpath = zip(pref_nodes[0:], pref_nodes[1:])

            pref_edges = []
            match_list = []
            aoi_list = []
            for u, v in edgesinpath:
                edge = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighing_name])[0]
                if 'geometry' in graph[u][v][edge]:
                    pref_edges.append(graph[u][v][edge]['geometry'])
                if 'match_id' in graph[u][v][edge]:
                    match_list.append(graph[u][v][edge]['match_id'])
                if 'AoI_rp100' in graph[u][v][edge]:
                    if isinstance(graph[u][v][edge]['AoI_rp100'], list):
                        aoi_list.extend(graph[u][v][edge]['AoI_rp100'])
                    else:
                        aoi_list.append(graph[u][v][edge]['AoI_rp100'])

            # remove al 0's from the AoI list
            aoi_list = [float(x) for x in aoi_list if (x != 0) and (x == x)]
            aoi_list = list(set(aoi_list))
            pref_edges = MultiLineString(pref_edges)
            pref_routes = pref_routes.append({'o_node': o[0], 'd_node': d[0], 'origin': o[1],
                                              'destination': d[1], 'AoIs': aoi_list, 'pref_path': pref_nodes,
                                              weighing_name: pref_route, 'match_ids': match_list,
                                              'geometry': pref_edges}, ignore_index=True)
    if save_shp:
        gdf_to_shp(pref_routes, os.path.join(file_output, '{}_pref_routes.shp'.format(name)))
        print("Preferred routes saved to {}".format(os.path.join(file_output, '{}_pref_routes.shp'.format(name))))

    if save_pickle:
        pref_routes[['origin', 'destination', 'AoIs', 'pref_path', weighing_name,
                     'match_ids']].to_pickle(os.path.join(file_output, '{}_pref_routes.pkl'.format(name)))
        print("Preferred routes saved to {}".format(os.path.join(file_output, '{}_pref_routes.pkl'.format(name))))

    return pref_routes


def calc_avg_speed(graph, road_type_col_name, save_csv=False, save_path=None):
    """Calculates the average speed from OSM roads, per road type
    Args:
        graph: NetworkX graph with road types
        road_type_col_name: name of the column which holds the road types ('highway' in OSM)
        save_csv [boolean]: to save a csv or not
        save_path [string]: path to save the csv to
    Returns:
        dataframe with the average road speeds per road type
    """
    # Create a dataframe of all road types
    exceptions = list(set([str(edata[road_type_col_name]) for u, v, edata in graph.edges.data() if isinstance(edata[road_type_col_name], list)]))
    types = list(set([str(edata[road_type_col_name]) for u, v, edata in graph.edges.data() if isinstance(edata[road_type_col_name], str)]))
    all_road_types = exceptions + types
    df = pd.DataFrame({'road_types': all_road_types, 'avg_speed': 0})

    # calculate average speed
    for i in range(len(df)):
        roadtype = df.road_types[i]
        all_edges = [(u, v, edata['maxspeed'], edata['length']) for u, v, edata in graph.edges.data() if
                     (str(edata[road_type_col_name]) == roadtype) & ('maxspeed' in edata)]
        all_avg = []
        all_l = []
        for u, v, s, l in all_edges:
            if isinstance(s, list):
                ns = []
                for ss in s:
                    if not any(c.isalpha() for c in ss) and not (';' in ss) and not ('|' in ss):
                        ns.append(int(ss))
                    elif not any(c.isalpha() for c in ss) and ';' in ss:
                        ns.extend([int(x) for x in ss.split(';') if x.isnumeric()])
                    elif not any(c.isalpha() for c in ss) and '|' in ss:
                        ns.extend([int(x) for x in ss.split('|') if x.isnumeric()])
                    elif ' mph' in ss:
                        ns.append(int(ss.split(' mph')[0]) * 1.609344)
                if len(ns) > 0:
                    ss = sum(ns) / len(ns)
                else:
                    continue
            elif isinstance(s, str):
                if not any(c.isalpha() for c in s) and not (';' in s) and not ('|' in s):
                    ss = int(s)
                elif not any(c.isalpha() for c in s) and ';' in s:
                    ss = mean([int(x) for x in s.split(';') if x.isnumeric()])
                elif not any(c.isalpha() for c in s) and '|' in s:
                    ss = mean([int(x) for x in s.split('|') if x.isnumeric()])
                elif ' mph' in s:
                    ss = int(s.split(' mph')[0]) * 1.609344
                else:
                    continue
            all_avg.append(ss * l)
            all_l.append(l)
            df.iloc[i, 1] = sum(all_avg) / sum(all_l)

    if save_csv:
        if not save_path.endswith('.csv'):
            save_path = save_path + '.csv'
        df.to_csv(save_path)
        print("Saved the average speeds per road type to: {}".format(save_path))

    return df


def assign_avg_speed(graph, avg_road_speed, road_type_col_name, save_path=None, save_shp=False, save_pickle=False):
    """Assigns the average speed to roads in an existing (OSM) graph
    """
    # make a list of strings instead of just a string of the road types column
    avg_road_speed["road_types"] = avg_road_speed["road_types"].astype(str)

    # calculate the average maximum speed per edge and assign the ones that don't have a value
    for u, v, k, edata in graph.edges.data(keys=True):
        road_type = str(edata[road_type_col_name])
        if 'maxspeed' in edata:
            max_speed = edata['maxspeed']
            if isinstance(max_speed, list):
                ns = []
                for ms in max_speed:
                    if not any(c.isalpha() for c in ms) and not (';' in ms) and not ('|' in ms):
                        ns.append(int(ms))
                    elif not any(c.isalpha() for c in ms) and ';' in ms:
                        ns.extend([int(x) for x in ms.split(';') if x.isnumeric()])
                    elif not any(c.isalpha() for c in ms) and '|' in ms:
                        ns.extend([int(x) for x in ms.split('|') if x.isnumeric()])
                    elif ' mph' in ms:
                        ns.append(int(ms.split(' mph')[0]) * 1.609344)
                if len(ns) > 0:
                    graph[u][v][k]['avgspeed'] = sum(ns) / len(ns)
                else:
                    graph[u][v][k]['avgspeed'] = avg_road_speed.loc[avg_road_speed['road_types'] == road_type, 'avg_speed'].iloc[0]
            elif isinstance(max_speed, str):
                if not any(c.isalpha() for c in max_speed) and not (';' in max_speed) and not ('|' in max_speed):
                    graph[u][v][k]['avgspeed'] = int(max_speed)
                elif not any(c.isalpha() for c in max_speed) and ';' in max_speed:
                    graph[u][v][k]['avgspeed'] = mean([int(x) for x in max_speed.split(';') if x.isnumeric()])
                elif not any(c.isalpha() for c in max_speed) and '|' in max_speed:
                    graph[u][v][k]['avgspeed'] = mean([int(x) for x in max_speed.split('|') if x.isnumeric()])
                elif ' mph' in max_speed:
                    graph[u][v][k]['avgspeed'] = int(max_speed.split(' mph')[0]) * 1.609344
                else:
                    graph[u][v][k]['avgspeed'] = avg_road_speed.loc[avg_road_speed['road_types'] == road_type, 'avg_speed'].iloc[0]
        else:
            if ']' in road_type:
                avg_speed = int([s for r, s in zip(avg_road_speed['road_types'], avg_road_speed['avg_speed']) if set(road_type[2:-2].split("', '")) == set(r[2:-2].split("', '"))][0])
                graph[u][v][k]['avgspeed'] = avg_speed
            else:
                graph[u][v][k]['avgspeed'] = avg_road_speed.loc[avg_road_speed['road_types'] == road_type, 'avg_speed'].iloc[0]

    if save_shp:
        graph_to_shp(graph, os.path.join(save_path, '_edges.shp'), os.path.join(save_path, '_nodes.shp'))
        print("Saving graph to shapefile in: {}".format(save_path))
    if save_pickle:
        nx.write_gpickle(graph, os.path.join(save_path, 'graph.gpickle'))
        print("Saving graph to pickle: {}".format(os.path.join(save_path, 'graph.gpickle')))

    return graph


def hazard_intersect_graph(graph, hazard, hazard_name, name, agg='max', save_path=None, save_shp=False, save_pickle=False):
    """adds hazard values (flood/earthquake/etc) to the roads in a graph
    Args:
        graph [networkX graph]
        hazard [string]: full path to hazard data
        agg [string]: choose from max, min or mean; when multiple sections of a road
            are overlapping, aggregate the data in this way
    Returns:
        Graph with the added hazard data, when there is no hazard, the values is 0
    """
    # import and append the hazard data
    for h, hn in zip(hazard, hazard_name):
        if h.endswith('.tif'):
            # GeoTIFF
            src = rasterio.open(h)

            # check which road is overlapping with the flood and append the flood depth to the graph
            for u, v, k, edata in graph.edges.data(keys=True):
                if 'geometry' in edata:
                    # check how long the road stretch is and make a point every other meter
                    nr_points = round(edata['length'])
                    if nr_points == 1:
                        coords_to_check = list(edata['geometry'].boundary)
                    else:
                        coords_to_check = [edata['geometry'].interpolate(i/float(nr_points - 1), normalized=True) for i in range(nr_points)]
                    crds = []
                    for c in coords_to_check:
                        # check if part of the linestring is inside the flood extent
                        if (src.bounds.left < c.coords[0][0] < src.bounds.right) and (src.bounds.bottom < c.coords[0][1] < src.bounds.top):
                            crds.append(c.coords[0])
                    if crds:
                        # the road lays inside the flood extent
                        if agg == 'max':
                            if (max([x.item(0) for x in src.sample(crds)]) > 999999) | (max([x.item(0) for x in src.sample(crds)]) < -999999):
                                # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                                graph[u][v][k][hn] = 0
                            else:
                                graph[u][v][k][hn] = max([x.item(0) for x in src.sample(crds)])
                        elif agg == 'min':
                            if (min([x.item(0) for x in src.sample(crds)]) > 999999) | (min([x.item(0) for x in src.sample(crds)]) < -999999):
                                # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                                graph[u][v][k][hn] = 0
                            else:
                                graph[u][v][k][hn] = min([x.item(0) for x in src.sample(crds)])
                        elif agg == 'mean':
                            if (mean([x.item(0) for x in src.sample(crds)]) > 999999) | (mean([x.item(0) for x in src.sample(crds)]) < -999999):
                                # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                                graph[u][v][k][hn] = 0
                            else:
                                graph[u][v][k][hn] = mean([x.item(0) for x in src.sample(crds)])
                        else:
                            warnings.warn("No aggregation method is chosen ('max', 'min' or 'mean).")
                    else:
                        graph[u][v][k][hn] = 0
                else:
                    graph[u][v][k][hn] = 0

        elif h.endswith('.shp'):
            # Shapefile
            gdf = gpd.read_file(h)
            spatial_index = gdf.sindex

            for u, v, k, edata in graph.edges.data(keys=True):
                if 'geometry' in edata:
                    possible_matches_index = list(spatial_index.intersection(edata['geometry'].bounds))
                    possible_matches = gdf.iloc[possible_matches_index]
                    precise_matches = possible_matches[possible_matches.intersects(edata['geometry'])]

                    if not precise_matches.empty:
                        if agg == 'max':
                            graph[u][v][k][hn] = precise_matches[hn].max()
                        if agg == 'min':
                            graph[u][v][k][hn] = precise_matches[hn].min()
                        if agg == 'mean':
                            graph[u][v][k][hn] = precise_matches[hn].mean()
                    else:
                        graph[u][v][k][hn] = 0
                else:
                    graph[u][v][k][hn] = 0

        else:
            print("The hazard data is not a GEOTIFF or Shapefile. Please input only these filetypes. Restart the analysis.")

    if save_shp:
        graph_to_shp(graph, os.path.join(save_path, name + '_edges.shp'), os.path.join(save_path, name + '_nodes.shp'))
    if save_pickle:
        nx.write_gpickle(graph, os.path.join(save_path, name + '_graph.gpickle'))

    return graph


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





# CRITICALITY FUNCTION
def criticality_single_link(graph, IdName, roadUsageData, aadtNames):
    """Calculates the alternative detour distance for each road segment if that road segement is blocked.
    Args:
        graph [networkX graph]
    Returns:
        dataframe with road criticality measured with alternative distance if you take away one edge at a time
    """

    # now only multidigraphs and graphs are used
    if type(graph) == nx.classes.graph.Graph:
        graph = nx.MultiGraph(graph)

    gdf = osmnx.graph_to_gdfs(graph, nodes=False)

    # all edges in the graph will be removed one by one
    list_remove = list(graph.edges.data(keys=True))

    for e_remove in list_remove:
        # edge to remove
        u, v, k, data = e_remove

        the_id = data[IdName]

        # make a copy of the graph
        H = graph.copy()

        # remove edge
        H.remove_edge(u, v, k)

        # check if the nodes are normally connected
        if nx.has_path(H, u, v):
            # calculate the alternative distance if that edge is unavailable
            alt_dist = nx.dijkstra_path_length(H, u, v, weight='length')

            # append alternative route nodes
            alt_nodes = nx.dijkstra_path(H, u, v)
            alt_nodes = ', '.join(map(str, alt_nodes))  # make it a string to save in shp

            # calculate the difference in distance
            dif_dist = alt_dist - data['length']
        else:
            alt_dist = np.NaN
            alt_nodes = np.NaN
            dif_dist = np.NaN

        # add the values to the geodataframe
        gdf.loc[gdf[IdName] == the_id, 'alt_dist_m'] = alt_dist
        gdf.loc[gdf[IdName] == the_id, 'alt_nodes'] = alt_nodes
        gdf.loc[gdf[IdName] == the_id, 'dif_dist_m'] = dif_dist

    if not roadUsageData.empty:
        if 'operating_cost' in roadUsageData.columns:
            # for now: all missing values for the AADT counts are replaced by 0. TODO: change?
            for aadt in aadtNames:
                gdf[aadt].fillna(0, inplace=True)

            # calculate the costs for the routes with and without detour with the AADT
            # detour possible
            operating_costs = np.multiply(np.sum(np.multiply(np.array(roadUsageData['operating_cost'].T), np.array(gdf[aadtNames])), axis=1), (np.array(gdf['dif_dist_m']) / 1000))
            operating_costs = [round(num, 2) for num in list(operating_costs)]
            gdf['cost_det'] = operating_costs

        if ('daily_loss_disruption' in roadUsageData.columns) & ('passengers_w_driver' in roadUsageData.columns):
            # no detour possible
            daily_loss = np.multiply(np.sum(np.multiply(np.array(roadUsageData['passengers_w_driver'].T), np.array(gdf.loc[gdf['dif_dist_m'].isnull()][aadtNames])), axis=1), roadUsageData['daily_loss_disruption'].iloc[0])
            daily_loss = [round(num, 2) for num in list(daily_loss)]
            gdf.loc[gdf['dif_dist_m'].isnull(), 'cost_no_d'] = daily_loss

    return gdf


def criticality_single_link_osm(graph):
    """
    :param graph: graph on which to run analysis (MultiDiGraph)
    :return: df with dijkstra detour distance and path results
    """
    # create a geodataframe from the graph
    gdf = osmnx.graph_to_gdfs(graph, nodes=False)

    # list for the length of the alternative routes
    alt_dist_list = []
    alt_nodes_list = []
    dif_dist_list = []
    for e_remove in list(graph.edges.data(keys=True)):
        u, v, k, data = e_remove

        # if data['highway'] in attr_list:
        # remove the edge
        graph.remove_edge(u, v, k)

        if nx.has_path(graph, u, v):
            # calculate the alternative distance if that edge is unavailable
            alt_dist = nx.dijkstra_path_length(graph, u, v, weight='length')
            alt_dist_list.append(alt_dist)

            # append alternative route nodes
            alt_nodes = nx.dijkstra_path(graph, u, v)
            alt_nodes_list.append(alt_nodes)

            # calculate the difference in distance
            dif_dist_list.append(alt_dist - data['length'])
        else:
            alt_dist_list.append(np.NaN)
            alt_nodes_list.append(np.NaN)
            dif_dist_list.append(np.NaN)

        # add edge again to the graph
        graph.add_edge(u, v, k, **data)

    # Add the new columns to the geodataframe
    gdf['alt_dist'] = alt_dist_list
    gdf['alt_nodes'] = alt_nodes_list
    gdf['diff_dist'] = dif_dist_list

    return gdf


def criticality_multi_link_hazard_OD(graph, prefRoutes, weighingName, hazardName, threshold, crs_):
    """Calculates the criticality of origins and destinations"""
    # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
    gdf = gpd.GeoDataFrame(columns=['disrupted', 'extra_{}'.format(weighingName), 'no detour', 'origin', 'destination', 'odpair',
                                    'd_disrupt', 'o_disrupt', 'd_{}'.format(hazardName), 'o_{}'.format(hazardName), 'geometry'],
                           geometry='geometry', crs={'init': 'epsg:{}'.format(crs_)})

    to_remove = [(e[0], e[1], e[2]) for e in graph.edges.data(keys=True) if (e[-1][hazardName] > threshold) & (
                'bridge' not in e[-1])]
    graph.remove_edges_from(to_remove)

    for ii in range(len(prefRoutes.index)):
        o, d = prefRoutes.iloc[ii][['o_node', 'd_node']]
        o = int(o)
        d = int(d)

        extra_time = np.NaN

        # check if the nodes are still connected
        if nx.has_path(graph, o, d):
            # calculate the alternative distance if that edge is unavailable
            alt_route = nx.dijkstra_path_length(graph, o, d, weight=weighingName)

            # save preferred route nodes
            pref_nodes = nx.dijkstra_path(graph, o, d, weight=weighingName)

            # subtract the length/time of the optimal route from the alternative route
            extra_time = alt_route - prefRoutes.iloc[ii][weighingName]

            if prefRoutes.iloc[ii][weighingName] != alt_route:
                # the alternative route is different from the optimal route
                disrupted = 1
                detour = "alt_route"

                # found out which edges belong to the preferred path
                edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

                pref_edges = []
                for u, v in edgesinpath:
                    # get edge with the lowest weighing if there are multiple edges that connect u and v
                    edge_key = sorted(graph[u][v], key=lambda x: graph[u][v][x][weighingName])[0]
                    if 'geometry' in graph[u][v][edge_key]:
                        pref_edges.append(graph[u][v][edge_key]['geometry'])
                    else:
                        pref_edges.append(LineString([graph.nodes[u]['geometry'], graph.nodes[v]['geometry']]))

                # compile the road segments into one geometry
                pref_edges = MultiLineString(pref_edges)
            else:
                # the alternative route is the same as the optimal route
                disrupted = 0
                detour = "same"
                pref_edges = prefRoutes.iloc[ii]['geometry']
        else:
            # append to calculation dataframe
            disrupted = 1
            detour = "no_detour"
            pref_edges = prefRoutes.iloc[ii]['geometry']

        gdf = gdf.append({'disrupted': disrupted, 'extra_{}'.format(weighingName): extra_time, 'no detour': detour,
                          'origin': str(prefRoutes.iloc[ii]['origin']),
                          'destination': str(prefRoutes.iloc[ii]['destination']),
                          'odpair': str(prefRoutes.iloc[ii]['origin']) + ' to ' + str(
                              prefRoutes.iloc[ii]['destination']),
                          'd_disrupt': prefRoutes.iloc[ii]['d_disrupt'],
                          'o_disrupt': prefRoutes.iloc[ii]['o_disrupt'],
                          'd_{}'.format(hazardName): prefRoutes.iloc[ii]['d_{}'.format(hazardName)],
                          'o_{}'.format(hazardName): prefRoutes.iloc[ii]['o_{}'.format(hazardName)],
                          'geometry': pref_edges}, ignore_index=True)

    return gdf


def criticality_multi_link_hazard(graph, attribute_name, min_threshold, idName):
    """
    The function removes all links of a variable that have a minimum value
    of min_threshold. For each link it calculates the alternative path, af
    any available. This function only removes one group at the time and saves the data from removing that group.

    Arguments:
        graph [networkx graph] = the graph with at least the columns that you use in group en sort
        attribute_name [string] = name of the attribute that indicates whether a road segment should be removed
        min_threshold [numeric] = the minimum value of the attribute by which the roads should be removed
    Returns:
        gdf [geopandas dataframe]
    """
    # now only multigraphs and graphs are used
    if type(graph) == nx.classes.graph.Graph:
        graph = nx.MultiGraph(graph)

    # Create a geodataframe from the full graph
    gdf = osmnx.graph_to_gdfs(graph, nodes=False)
    gdf[idName] = gdf[idName].astype(str)

    # Check if there is only one or more hazards
    if (isinstance(attribute_name, list)) & (len(attribute_name) == 1):
        attribute_name = attribute_name[0]
    elif (isinstance(attribute_name, list)) & (len(attribute_name) > 1):
        warnings.warn("This feature (multiple hazard criticality calculation) is not yet implemented.")

    # Create the edgelist that consist of edges that should be removed
    edges_remove = [e for e in graph.edges.data(keys=True) if attribute_name in e[-1]]
    edges_remove = [e for e in edges_remove if (e[-1][attribute_name] > min_threshold) & ('bridge' not in e[-1])]

    graph.remove_edges_from(edges_remove)

    # dataframe for saving the calculations of the alternative routes
    df_calculated = pd.DataFrame(columns=['u', 'v', idName, 'alt_dist', 'alt_nodes', 'connected'])

    for i, edges in enumerate(edges_remove):
        u, v, k, edata = edges

        # check if the nodes are still connected
        if nx.has_path(graph, u, v):
            # calculate the alternative distance if that edge is unavailable
            alt_dist = nx.dijkstra_path_length(graph, u, v, weight='length')

            # save alternative route nodes
            alt_nodes = nx.dijkstra_path(graph, u, v)

            # append to calculation dataframe
            df_calculated = df_calculated.append({'u': u, 'v': v, idName: str(edata[idName]), 'alt_dist': alt_dist,
                                                  'alt_nodes': alt_nodes, 'connected': 1}, ignore_index=True)
        else:
            # append to calculation dataframe
            df_calculated = df_calculated.append({'u': u, 'v': v, idName: str(edata[idName]), 'alt_dist': np.NaN,
                                                  'alt_nodes': np.NaN, 'connected': 0}, ignore_index=True)

    # Merge the dataframes
    gdf = gdf.merge(df_calculated, how='left', on=['u', 'v', idName])

    # calculate the difference in distance
    gdf['diff_dist'] = [dist - length if dist == dist else np.NaN for (dist, length) in zip(gdf['alt_dist'], gdf['length'])]

    return gdf


def gdf_to_shp(gdf, result_shp):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    for col in gdf.columns:
        if gdf[col].dtype == np_object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(result_shp, driver='ESRI Shapefile', encoding='utf-8')


def create_graph_europe(ToolFolder, AllOutput, name, InputDict, crs):
    """Creates the graph that is then used for single/multi-link analysis
    Args:
        ToolFolder [string]: absolute path of the location of the main tool script
        AllOutput [string]: absolute path to the location where to save all files (./GIS/output)
    Returns:
        G [NetworkX graph]
    """
    # input
    crs_ = {'init': 'epsg:{}'.format(crs)}

    # tools
    osm_convert_path = os.path.join(ToolFolder, "osmconvert64.exe")
    osm_filter_path = os.path.join(ToolFolder, "osmfilter.exe")

    aadt_path = None  # optional, if you have UNECE e-road data, point to this path (.xlsx), otherwise None
    classify_eroads = False  # True ifq you want to classify the roads by e-road, otherwise false
    rp_choice = 100  # choose the return period

    # initialise the variables
    # 'length', 'alt_dist', 'dif_dist' <- names for distance measurement
    # 'time', 'alt_time', 'dif_s' <-- names for time measurement
    # list = [weighing_name, weighing, dif_name]
    weighing = 'time'  # or distance
    if weighing == 'distance':
        weighing_names = ['length', 'alt_dist', 'dif_dist']
    elif weighing == 'time':
        weighing_names = ['time', 'alt_time', 'dif_s']

    # import data from Kees' model
    gdf_flood = import_flood_data(InputDict['floods_path'], InputDict['incl_nuts'], InputDict['incl_countries'],
                                  crs, save_shp=False)

    # make integers from the flood data osm_id colomn
    gdf_flood['osm_id'] = pd.to_numeric(gdf_flood['osm_id'])

    # create a list of all AoI id numbers and save to a pickle for the stochastic analysis
    all_aois_in_area = list(gdf_flood.loc[(gdf_flood['NUTS-0'].isin(InputDict['incl_countries'])) &
                                          (gdf_flood['AoI_rp{}'.format(rp_choice)].notnull()),
                                          'AoI_rp{}'.format(rp_choice)].unique())
    pickle.dump(all_aois_in_area, open(os.path.join(AllOutput, "unique_aois_{}.p".format(name)), 'wb'))

    # TODO: make it possible that users can retrieve more data from OSM and link it to the graph roads
    if classify_eroads:
        # Fetch e-roads data with OSM id
        dict_eroads = fetch_e_roads_data(InputDict['osm_path'], InputDict['incl_nuts'], InputDict['incl_countries'])
    else:
        dict_eroads = None

    # get poly file of country/NUTS-3 regions of choice
    poly_files_europe(os.path.join(AllOutput, name + '.poly'), InputDict['clip_shp_path'])
    clip_osm(osm_convert_path, InputDict['pbf_europe_path'], os.path.join(AllOutput, name + '.poly'),
                os.path.join(AllOutput, name + '.o5m'))
    filter_osm(osm_filter_path, os.path.join(AllOutput, name + '.o5m'),
                  os.path.join(AllOutput, name + '_till_secondary.o5m'))

    # create a graph
    G_original = graph_from_osm(os.path.join(AllOutput, name + '_till_secondary.o5m'), multidirectional=False)

    # match flood data with road network and possibly e-roads
    # match for each road segment the intersecting floods
    G = match_ids(G_original, gdf_flood, value_column="val_rp{}".format(rp_choice),
                group_column="AoI_rp{}".format(rp_choice), dict_eroads=dict_eroads, aadt_path=aadt_path)

    # add other variables: time
    # Define and assign average speeds; or take the average speed from an existing CSV
    avg_speeds = calc_avg_speed(G, 'highway', save_csv=True,
                                save_path=os.path.join(AllOutput, "average_speed_osm_road_type_{}.csv".format(name)))
    G = assign_avg_speed(G, avg_speeds, 'highway')

    # make a time value of seconds, length of road streches is in meters
    for u, v, k, edata in G.edges.data(keys=True):
        hours = (edata['length'] / 1000) / edata['avgspeed']
        G[u][v][k][weighing] = hours * 3600

    # save the graph
    nx.write_gpickle(G, os.path.join(AllOutput, '{}_graph.gpickle'.format(name)))
    graph_to_shp(G, os.path.join(AllOutput, '{}_edges.shp'.format(name)),
                 os.path.join(AllOutput, '{}_nodes.shp'.format(name)))

    return G


# VISUALISATION FUNCTIONS
def vis_graph(graph):
    # elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] > 0.5]
    # esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] <= 0.5]

    pos = nx.spring_layout(graph)  # positions for all nodes

    # nodes
    nx.draw_networkx_nodes(graph, pos, node_size=10)

    # edges
    nx.draw_networkx_edges(graph, pos, width=6)

    # labels
    nx.draw_networkx_labels(graph, pos, font_size=10, font_family='sans-serif')
    plt.figure(1, figsize=(20, 20))
    plt.axis('off')
    plt.show()


def plot_heatmap(df, plot_title, y_label, save_path, aggregate=False, agg_type='mean'):
    """Plots the heatmap for connectivity between OD pairs
    Args:
        df [pandas dataframe]: dataframe with the origin, destination (named 'destinatio' because a shapefile column
        name cannot have more than 10 characters) and value of e.g. distance/time/cost
        plot_title [string]: title of the plot
        y_label [string]: name of the measured variable as y-axis label (add unit like "[X]")
        save_path [string]: path to file to save (with extension)
        aggregate [bool]: if False (default), no aggregation occurs. If True, the data is grouped by origin and
        destination and the measuring parameter (the 3rd column besides origin and destination) is aggregated via agg_type.
        agg_type [string/method of aggregation]: aggregation method
    """
    param = df.columns[~df.columns.isin(['origin', 'destinatio'])][0]
    max_val = df[param].max()

    if aggregate:
        no_detour = df.loc[df[param].isnull()]
        no_detour[param] = 99999
        df = df.loc[df[param].notnull()]

        if agg_type == 'std':
            df = df.groupby(['origin', 'destinatio'])[param].std(ddof=0).reset_index()
        else:
            df = df.groupby(['origin', 'destinatio'])[param].agg(agg_type).reset_index()

        max_val = df[param].max()
        no_detour = no_detour.groupby(['origin', 'destinatio'])[param].agg('mean').reset_index()
        df = pd.concat([df, no_detour], ignore_index=True, sort=False)
        df.sort_values(param, inplace=True)
        df.drop_duplicates(['origin', 'destinatio'], inplace=True)

    # duplicate the origin / destination column and change origin for destination and destination for origin, to fill the whole heatmap
    df2 = pd.DataFrame({param: df[param], 'origin': df['destinatio'], 'destinatio': df['origin']})
    df = pd.concat([df, df2], ignore_index=True, sort=False)
    a = df.pivot(index='origin', columns='destinatio', values=param)
    ylabs = list(a.index)
    xlabs = list(a.columns)

    fig, ax = plt.subplots(figsize=(20, 20))
    im = ax.imshow(a, cmap='RdBu_r', vmin=0, vmax=max_val,
                   extent=[0, len(xlabs), 0, len(ylabs)],
                   interpolation='none', origin='lower')

    # We want to show all ticks...
    plt.xticks([x - 0.5 for x in list(range(1, len(xlabs) + 1))], xlabs, rotation=90)
    plt.yticks([x - 0.5 for x in list(range(1, len(ylabs) + 1))], ylabs)

    # ... and label them with the respective list entries
    ax.set_xticklabels(xlabs)
    ax.set_yticklabels(ylabs)
    cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel(y_label, rotation=90)
    plt.title(plot_title)
    plt.show()
    fig.savefig(save_path)
    plt.close()

    print("Saved the figure to {}".format(save_path))


def df_stochastic_results(folder):
    files = [f for f in os.listdir(folder) if (os.path.isfile(os.path.join(folder, f))) and (f.endswith('.csv'))]

    # load data
    df = pd.DataFrame(columns=['AoI combinations', 'disrupted', 'avg extra time', 'AoI removed', 'no detour'])
    for f in files:
        df_new = pd.read_csv(os.path.join(folder, f))
        df = pd.concat([df, df_new], ignore_index=True, sort=False)

    df['AoI combinations'] = df['AoI combinations'].astype(int)
    return df


def combine_finished_stochastic(finished_folder):
    """Combines the separate csv files create by the parallel processed stochastic results.
    Args:
        input_path: path to the folder where the separate csv's are saved
        output_path: output path, full path to the csv that is merged from all csv's

    Returns:
        None
    """
    folders = os.listdir(finished_folder)  # folder correspond to items of the combs_list defined before

    for folder in folders:
        files = os.listdir(os.path.join(finished_folder, folder))
        df = pd.read_csv(os.path.join(finished_folder, folder, files[0]))
        for file in files[1:]:
            df_add = pd.read_csv(os.path.join(finished_folder, folder, file))
            df = pd.concat([df, df_add], sort='False')
        df.to_csv(os.path.join(finished_folder, "aoi_{}.csv".format(folder.split(".")[0])))


def add_missing_geoms_graph(graph, geom_name='geometry'):
    # Not all nodes have geometry attributed (some only x and y coordinates) so add a geometry columns
    nodes_without_geom = [n[0] for n in graph.nodes(data=True) if geom_name not in n[-1]]
    for nd in nodes_without_geom:
        graph.nodes[nd][geom_name] = Point(graph.nodes[nd]['x'], graph.nodes[nd]['y'])

    edges_without_geom = [e for e in graph.edges.data(keys=True) if geom_name not in e[-1]]
    for ed in edges_without_geom:
        graph[ed[0]][ed[1]][ed[2]][geom_name] = LineString([graph.nodes[ed[0]][geom_name], graph.nodes[ed[1]][geom_name]])

    return graph
