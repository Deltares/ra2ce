# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""
import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)

import geopandas as gpd
from shapely.geometry import mapping
import rasterio
import shapely
from rasterio.mask import mask
from rasterio.features import shapes
from tqdm import tqdm
import logging
import time
import networkx as nx
import osmnx
from .direct_lookup import *


class DirectAnalyses:
    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

    def road_damage(self):
        gdf = self.graphs['base_network_hazard']
        if self.graphs['base_network_hazard'] is None:
            gdf = gpd.read_feather(self.config['files']['base_network_hazard'])


        # TODO: This should probably not be done here, but at the create network function
        # apply road mapping to fewer types
        road_mapping_dict = lookup_road_mapping()
        gdf.rename(columns={'highway': 'infra_type'}, inplace=True)
        gdf['road_type'] = gdf['infra_type']
        gdf = gdf.replace({"road_type": road_mapping_dict})

        # TODO sometimes there are edges with multiple mappings
        # cleanup of gdf
        for column in gdf.columns:
            gdf[column] = gdf[column].apply(apply_cleanup)

        gdf.loc[gdf.lanes == 'nan', 'lanes'] = np.nan  # replace string nans with numpy nans
        gdf.lanes = gdf.lanes.astype('float')  # convert strings to floats (not int, because int cant have nan)

        # calculate direct damage
        road_gdf_damage = calculate_direct_damage(gdf)
        return road_gdf_damage

    def effectivity_measurements(self):
        gdf = self.graphs['base_graph_hazard']
        if self.graphs['base_graph_hazard'] is None:
            gdf = gpd.read_feather(self.config['files']['base_graph_hazard'])

        dfnew = pd.DataFrame(gdf.drop(columns='geometry'))
        # TODO: This should probably not be done here, but at the create network function
        # apply road mapping to fewer types
        road_mapping_dict = lookup_road_mapping()




        return dfnew

    def execute(self):
        """Executes the direct analysis."""
        for analysis in self.config['direct']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            starttime = time.time()

            if analysis['analysis'] == 'direct':
                gdf = self.road_damage()

            if analysis['analysis'] == 'effectivity_measurements':
                gdf = self.effectivity_measurements()

            output_path = self.config['output'] / analysis['analysis']
            if analysis['save_shp']:
                shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                save_gdf(gdf, shp_path)
            if analysis['save_csv']:
                csv_path = output_path / (analysis['name'].replace(' ', '_') + '.csv')
                del gdf['geometry']
                gdf.to_csv(csv_path, index=False)

            endtime = time.time()
            logging.info(f"----------------------------- Analysis '{analysis['name']}' finished. "
                         f"Time: {str(round(endtime - starttime, 2))}s  -----------------------------")


def calculate_direct_damage(road_gdf):
    """
    Calculates the direct damage for all road segments with exposure data using a depth-damage curve
    Arguments:
        *road_gdf* (GeoPandas DataFrame) :
    Returns:
        *road_gdf* () :
    """


    # apply the add_default_lanes function to add default number of lanes
    default_lanes_dict = lookup_road_lanes()
    df_lookup = pd.DataFrame.from_dict(default_lanes_dict)

    road_gdf['country'] = 'NL'
    road_gdf['default_lanes'] = df_lookup.lookup(road_gdf['road_type'], road_gdf['country'])
    road_gdf['lanes'].fillna(road_gdf['default_lanes'], inplace=True)
    road_gdf = road_gdf.drop(columns=['default_lanes', 'country'])
    # road_gdf.lanes = road_gdf.apply(lambda x: default_lanes_dict[country][x['road_type']] if pd.isnull(x['lanes']) else x['lanes'],
    #                           axis=1).copy()


    # load lookup tables
    lane_damage_correction = lookup_road_damage_correction()
    dict_max_damages = lookup_max_damages()
    max_damages_huizinga = lookup_max_damages_huizinga()
    interpolators = lookup_flood_curves()

    # Perform loss calculation for all road segments
    val_cols = [x for x in list(road_gdf.columns) if 'val' in x]

    # Remove all rows from the dataframe containing roads that don't intersect with floods
    df = road_gdf.loc[~(road_gdf[val_cols] == 0).all(axis=1)]
    hzd_names = [i.split('val_')[1] for i in val_cols]

    curve_names = [name for name in interpolators]

    # TODO: remove the old calculation, it is redundant, but still in the code for reference.
    use_old_calculation = False
    if use_old_calculation is True:
        for curve_name in interpolators:
            interpolator = interpolators[curve_name]  # select the right interpolator
            from tqdm import tqdm
            tqdm.pandas(desc=curve_name)
            df = df.progress_apply(lambda x: road_loss_estimation(x,   interpolator, hzd_names, dict_max_damages,
                                                                  max_damages_huizinga, curve_name, lane_damage_correction), axis=1)

    else:
        # This calculation is 60 times faster:
        df = road_loss_estimation2(df, interpolators, hzd_names, dict_max_damages, max_damages_huizinga, curve_names, lane_damage_correction)

    return df


def road_loss_estimation(x, interpolator, events, max_damages, max_damages_HZ, curve_name, lane_damage_correction,
                         **kwargs):
    """
    Carries out the damage estimation for a road segment using various damage curves

    Arguments:
        *x* (Geopandas Series) -- a row from the region GeoDataFrame with all road segments
        *interpolator* (SciPy interpolator object) -- the interpolator function that belongs to the damage curve
        *events* (List of strings) -- containing the names of the events: e.g. [rp10,...,rp500]
            scripts expects that x has the columns length_{events} and val_{events} which it needs to do the computation
        *max_damages* (dictionary) -- dictionary containing the max_damages per road-type; not yet corrected for the number of lanes
        *max_damages_HZ* (dictionary) -- dictionary containing the max_damages per road-type and number of lanes, for the Huizinga damage curves specifically
        *name_interpolator* (string) -- name of the max_damage dictionary; to save as column names in the output pandas DataFrame -> becomes the name of the interpolator = damage curve
        *lane_damage_correction (OrderedDict) -- the max_dam correction factors (see load_lane_damage_correction)

    Returns:
        *x* (GeoPandas Series) -- the input row, but with new elements: the waterdepths and inundated lengths per RP, and associated damages for different damage curves

    """
    #try:
    if True:
        # GET THE EVENT-INDEPENDENT METADATA FROM X
        road_type = x["road_type"]  # get the right road_type to lookup ...

        # abort the script for not-matching combinations of road_types and damage curves
        if ((road_type in ['motorway', 'trunk'] and curve_name not in ["C1", "C2", "C3", "C4", "HZ"]) or
            (road_type not in ['motorway', 'trunk'] and curve_name not in ["C5", "C6",
                                                                           "HZ"])):  # if combination is not applicable
            for event in events:  # generate (0,0,0,0,0) output for each event
                x["dam_{}_{}".format(curve_name, event)] = tuple([0] * 5)
            return x

        lanes = x["lanes"]  # ... and the right number of lanes

        # DO THE HUIZINGA COMPARISON CALCULATION
        if curve_name == "HZ":  # only for Huizinga
            # load max damages huizinga
            max_damage = apply_huizinga_max_dam(max_damages_HZ, road_type, lanes)  # dict lookup: [road_type][lanes]
            for event in events:
                depth = x["val_{}".format(event)]
                length = x["length_{}".format(event)]  # inundated length in km
                x["dam_{}_{}".format(curve_name, event)] = round(max_damage * interpolator(depth) * length, 2)

        # DO THE MAIN COMPUTATION FOR ALL THE OTHER CURVES
        else:  # all the other curves
            # LOWER AN UPPER DAMAGE ESTIMATE FOR THIS ROAD TYPE BEFORE LANE CORRECTION
            lower = max_damages["Lower"][road_type]  # ... the corresponding lower max damage estimate ...
            upper = max_damages["Upper"][road_type]  # ... and the upper max damage estimate

            # CORRECT THE MAXIMUM DAMAGE BASED ON NUMBER OF LANES
            lower = lower * apply_lane_damage_correction(lane_damage_correction, road_type, lanes)
            upper = upper * apply_lane_damage_correction(lane_damage_correction, road_type, lanes)

            max_damages_interpolated = [lower, (3 * lower + upper) / 4, (lower + upper) / 2, (lower + 3 * upper) / 4,
                                        upper]  # interpolate between upper and lower: upper, 25%, 50%, 75% and higher
            # if you change this, don't forget to change the length of the exception output as well!
            for event in events:
                depth = x["val_{}".format(event)]  # average water depth in cm
                length = x["length_{}".format(event)]  # inundated length in km

                results = [None] * len(
                    max_damages_interpolated)  # create empty list, which will later be coverted to a tuple
                for index, key in enumerate(
                    max_damages_interpolated):  # loop over all different damage functions; the key are the max_damage percentile
                    results[index] = round(interpolator(depth) * key * length,
                                           2)  # calculate damage using interpolator and round to eurocents
                x["dam_{}_{}".format(curve_name, event)] = tuple(results)  # save results as a new column to series x

    return x


def road_loss_estimation2(gdf, interpolators, events, max_damages, max_damages_huizinga, curve_names, lane_damage_correction):
    """
    Carries out the damage estimation for a road segment using various damage curves

    Arguments:
        *x* (Geopandas Series) -- a row from the region GeoDataFrame with all road segments
        *interpolator* (SciPy interpolator object) -- the interpolator function that belongs to the damage curve
        *events* (List of strings) -- containing the names of the events: e.g. [rp10,...,rp500]
            scripts expects that x has the columns length_{events} and val_{events} which it needs to do the computation
        *max_damages* (dictionary) -- dictionary containing the max_damages per road-type; not yet corrected for the number of lanes
        *max_damages_HZ* (dictionary) -- dictionary containing the max_damages per road-type and number of lanes, for the Huizinga damage curves specifically
        *name_interpolator* (string) -- name of the max_damage dictionary; to save as column names in the output pandas DataFrame -> becomes the name of the interpolator = damage curve
        *lane_damage_correction (OrderedDict) -- the max_dam correction factors (see load_lane_damage_correction)

    Returns:
        *x* (GeoPandas Series) -- the input row, but with new elements: the waterdepths and inundated lengths per RP, and associated damages for different damage curves

    """
    # create dataframe from gdf
    column_names = list(gdf.columns)
    column_names.remove('geometry')
    df = gdf[column_names]

    # fixing lanes
    df['lanes_copy'] = df['lanes'].copy()
    df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) >= 1.0, other=1.0)
    df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) <= 6.0, other=6.0)
    df['tuple'] = [tuple([0] * 5)] * len(df['lanes'])

    # pre-calculation of max damages per percentage (same for each C1-C6 category)
    df['lower_damage'] = df['road_type'].copy().map(max_damages["Lower"])
    df['upper_damage'] = df['road_type'].copy().map(max_damages["Upper"])

    df_lane_damage_correction = pd.DataFrame.from_dict(lane_damage_correction)
    df['lower_dam'] = df['lower_damage'] * df_lane_damage_correction.lookup(df['lanes'], df['road_type'])
    df['upper_dam'] = df['upper_damage'] * df_lane_damage_correction.lookup(df['lanes'], df['road_type'])
    # df['lower_dam'] = df.apply(lambda x: x.lower_damage * lane_damage_correction[x.road_type][x.lanes], axis=1)
    # df['upper_dam'] = df.apply(lambda x: x.upper_damage * lane_damage_correction[x.road_type][x.lanes], axis=1)

    # create separate column for each percentage (is faster then tuple)
    for percentage in [0, 25, 50, 75, 100]:
        df['damage_{}'.format(percentage)] = (df['upper_dam'] * percentage / 100) + (df['lower_dam'] * (100 - percentage) / 100)

    columns = []
    for curve_name in curve_names:
        for event in events:
            interpolator = interpolators[curve_name]
            if curve_name == 'HZ':

                df_max_damages_huizinga = pd.DataFrame.from_dict(max_damages_huizinga)
                df['max_dam_hz'] = df_max_damages_huizinga.lookup(df['lanes'], df['road_type'])
                # df['max_dam_hz'] = df.apply(lambda x: max_damages_huizinga[x.road_type][x.lanes], axis=1)

                df['dam_{}_{}'.format(curve_name, event)] = round(df['max_dam_hz'].astype(float)
                                                                  * interpolator(df['val_{}'.format(event)]).astype(float)
                                                                  * df['length_{}'.format(event)].astype(float), 2)
            else:
                for percentage in [0, 25, 50, 75, 100]:
                    df['dam_{}_{}_{}'.format(percentage, curve_name, event)] = round(df['damage_{}'.format(percentage)].astype(float) \
                                                                               * interpolator(df['val_{}'.format(event)]).astype(float) \
                                                                               * df['length_{}'.format(event)].astype(float), 2)

                df['dam_{}_{}'.format(curve_name, event)] = tuple(zip(df['dam_0_{}_{}'.format(curve_name, event)],
                                                                      df['dam_25_{}_{}'.format(curve_name, event)],
                                                                      df['dam_50_{}_{}'.format(curve_name, event)],
                                                                      df['dam_75_{}_{}'.format(curve_name, event)],
                                                                      df['dam_100_{}_{}'.format(curve_name, event)]))

                df = df.drop(columns=['dam_{}_{}_{}'.format(percentage, curve_name, event) for percentage in [0, 25, 50, 75, 100]])

            # change back to 0's if the combination doesnt exist
            if curve_name in ["C1", "C2", "C3", "C4"]:
                # first copy values with trunk to temp column. Then replace everywhere
                # except motorway with 0's, then copy files of trunk back
                df.loc[df['road_type'] == 'trunk', 'temp'] = 'dam_{}_{}'.format(curve_name, event)
                df.loc[df['road_type'] != 'motorway', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']
                df.loc[df['road_type'] == 'trunk', 'dam_{}_{}'.format(curve_name, event)] = df['temp']

            if curve_name in ["C5", "C6"]:
                df.loc[df['road_type'] == 'motorway', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']
                df.loc[df['road_type'] == 'trunk', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']

            columns.append('dam_{}_{}'.format(curve_name, event))

    gdf = pd.concat([gdf, df[columns]], axis=1)

    return gdf


def apply_lane_damage_correction(lane_damage_correction, road_type, lanes):
    """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
    if lanes < 1: # if smaller than the mapped value -> correct with minimum value
        lanes = 1
    if lanes > 6: # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
        lanes = 6
    return lane_damage_correction[road_type][lanes]


def apply_huizinga_max_dam(max_damages_huizinga, road_type, lanes):
    """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
    if lanes < 1: # if smaller than the mapped value -> correct with minimum value
        lanes = 1
    if lanes > 6: # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
        lanes = 6
    return max_damages_huizinga[road_type][lanes]


def apply_cleanup(x):
    """ Cleanup for entries in dataframe, where there is a list with two values for a single field.

     This happens when there is both a primary_link and a primary infra_type.
     x[0] indicates the values of the primary_link infra_type
     x[1] indicates the values of the primary infra_type
     """
    if x is None:
        return None
    if type(x) == list:
        return x[1]  # 1 means select primary infra_type
    else:
        return x


def save_gdf(gdf, save_path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = 'epsg:4326'  # TODO: decide if this should be variable with e.g. an output_crs configured
    from numpy import object as np_object
    for col in gdf.columns:
        if gdf[col].dtype == np_object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver='ESRI Shapefile', encoding='utf-8')
    logging.info("Results saved to: {}".format(save_path))


