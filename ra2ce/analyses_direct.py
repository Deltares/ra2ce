import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)

# Direct analyses
from collections import defaultdict, OrderedDict
import pickle
import pandas as pd
import geopandas as gpd
from boltons.iterutils import pairwise
from geopy.distance import vincenty
from natsort import natsorted
import matplotlib.pyplot as plt
from utils import load_config
from shapely.geometry import mapping
import rasterio
import shapely
from rasterio.mask import mask
from rasterio.features import shapes
import numpy as np
from tqdm import tqdm
from pathlib import Path
from create_network_from_osm_dump import generate_damage_input
import logging

LOG_FILENAME = os.path.join(os.path.dirname(folder), './log_ra2ce.log')
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

#### AT THIS POINT, YOU MAY WANT TO DO CLEANING OF YOUR NETWORK, FOR EXAMPLE USING THE cleanup_fetch_roads() in OSdaMage ####

### Apply the mapping of the road types
def import_road_mapping(file_path, sheet_name):
    """
    Creates a dictionary to create an aggregated list of road types; from an Excel file.

    Arguments:
        *file_path* (string) - path to the Excel file (should be located in the input_path dir.)
        *sheet_name* (string) - name of the Excel sheetname containing the data

    Returns:
        *road_mapping* (Default dictionary) - Default dictionary containing OSM 'highway' variables as keys and the aggregated group names as values, will return 'none when an uknown key is entered'
    """

    mapping = pd.read_excel(file_path,
                            sheet_name=sheet_name, index_col=0, usecols="A:B")
    mapping = mapping.T.to_dict(orient='records')[0]
    road_mapping = defaultdict(default_road, mapping)
    return road_mapping

def default_road(): #If the tagged road_type in OSM is unknown, use this value
    return 'none'


def line_length(line, ellipsoid='WGS-84', shipping=True):
    """Length of a line in meters, given in geographic coordinates

    Adapted from https://gis.stackexchange.com/questions/4022/looking-for-a-pythonic-way-to-calculate-the-length-of-a-wkt-linestring#answer-115285

    Arguments:
        line {Shapely LineString} -- a shapely LineString object with WGS-84 coordinates
        ellipsoid {String} -- string name of an ellipsoid that `geopy` understands (see
            http://geopy.readthedocs.io/en/latest/#module-geopy.distance)

    Returns:
        Length of line in meters
    """
    if shipping == True:
        if line.geometryType() == 'MultiLineString':
            return sum(line_length(segment) for segment in line)

        return sum(
            vincenty(tuple(reversed(a)), tuple(reversed(b)), ellipsoid=ellipsoid).kilometers
            for a, b in pairwise(line.coords)
        )

    else:
        if line.geometryType() == 'MultiLineString':
            return sum(line_length(segment) for segment in line)

        return sum(
            vincenty(a, b, ellipsoid=ellipsoid).kilometers ###WARNING TODO: WILL BE DEPRECIATED ####
            for a, b in pairwise(line.coords)
        )


def create_hzd_df(geometry, hzd_list, hzd_names):
    """
    Arguments:

        *geometry* (Shapely Polygon) -- shapely geometry of the region for which we do the calculation.
        *hzd_list* (list) -- list of file paths to the hazard files.
        *hzd_names* (list) -- list of names to the hazard files.

    Returns:
        *Geodataframe* -- GeoDataFrame where each row is a unique flood shape in the specified **region**.

    """

    ## MAKE GEOJSON GEOMETRY OF SHAPELY GEOMETRY FOR RASTERIO CLIP
    geoms = [mapping(geometry)]

    all_hzds = []

    ## LOOP OVER ALL HAZARD FILES TO CREATE VECTOR FILES
    for iter_, hzd_path in enumerate(hzd_list):
        # extract the raster values values within the polygon
        with rasterio.open(hzd_path) as src:
            out_image, out_transform = mask(src, geoms, crop=True)

            # change into centimeters and make any weird negative numbers -1 (will result in less polygons)
            out_image[out_image <= 0] = -1
            out_image = np.array(out_image * 100, dtype='int32')

            # vectorize geotiff
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v)
                in enumerate(
                shapes(out_image[0, :, :], mask=None, transform=out_transform)))

            # save to geodataframe, this can take quite long if you have a big area
            gdf = gpd.GeoDataFrame.from_features(list(results))


            # Confirm that it is WGS84
            gdf.crs = {'init': 'epsg:4326'}
            #gdf.crs = {'init': 'epsg:3035'}
            #gdf.to_crs(epsg=4326,inplace=True) #convert to WGS84



            gdf = gdf.loc[gdf.raster_val >= 0]
            gdf = gdf.loc[gdf.raster_val < 5000]  # remove outliers with extreme flood depths (i.e. >50 m)
            gdf['geometry'] = gdf.buffer(0)

            gdf['hazard'] = hzd_names[iter_]
            all_hzds.append(gdf)
    return pd.concat(all_hzds)


def intersect_hazard(x, hzd_reg_sindex, hzd_region):
    """
    Arguments:

        *x* (road segment) -- a row from the region GeoDataFrame with all road segments.
        *hzd_reg_sindex* (Spatial Index) -- spatial index of hazard GeoDataFrame
        *hzd_region* (GeoDataFrame) -- hazard GeoDataFrame

    Returns:
        *geometry*,*depth* -- shapely LineString of flooded road segment and the average depth

    """
    matches = hzd_region.iloc[list(hzd_reg_sindex.intersection(x.geometry.bounds))].reset_index(drop=True)
    try:
        if len(matches) == 0:
            return x.geometry, 0
        else:
            append_hits = []
            for match in matches.itertuples():
                inter = x.geometry.intersection(match.geometry)
                if inter.is_empty == True:
                    continue
                else:
                    if inter.geom_type == 'MultiLineString':
                        for interin in inter:
                            append_hits.append((interin, match.raster_val))
                    else:
                        append_hits.append((inter, match.raster_val))

            if len(append_hits) == 0:
                return x.geometry, 0
            elif len(append_hits) == 1:
                return append_hits[0][0], int(append_hits[0][1])
            else:
                return shapely.geometry.MultiLineString([x[0] for x in append_hits]), int(
                    np.mean([x[1] for x in append_hits]))
    except Exception as e:
        print(e)
        return x.geometry, 0

def apply_road_mapping(road_gdf):
    """
    Apply a road mapping from a larger set of infra_types
    (e.g. [motorway, motorway_link, ..., X, X_link] to a
    smaller set of types, called road_types
    (e.g. [motorway, ..., X]

    Arguments:
        *road_gdf* (GeoPandas Dataframe) : should have a column 'infra_types'

    Returns:
        *road_gdf* (GeoPandas Dataframe): the same gdf, with an extra column 'road_types'
    """
    # TODO: the stuff in this function is now split over to many different functions, which can be merged
    # MAP OSM INFRA TYPES TO A SMALLER GROUP OF ROAD_TYPES
    path_settings = load_config()['paths']['settings']
    road_mapping_path = os.path.join(path_settings, 'OSM_infratype_to_roadtype_mapping.xlsx')
    road_mapping_dict = import_road_mapping(road_mapping_path, 'Mapping')
    road_gdf['road_type'] = road_gdf.infra_type.apply( \
        lambda x: road_mapping_dict[x])  # add a new column 'road_type' with less categories
    return road_gdf


def add_hazard_data_to_road_network(road_gdf,region_path,hazard_path,tolerance = 0.00005):
    """
    Adds the hazard data to the road network, i.e. creates an exposure map

    Arguments:
        *road_gdf* (GeoPandas DataFrame) : The road network without hazard data
        *region_path* (string) : Path to the shapefile describing the regional boundaries
        *hazard_path* (string) : Path to file or folder containg the hazard maps
           -> If this refers to a file: only run for this file
           -> If this refers to a folder: run for all hazard maps in this folder
        *tolerance* (float) : Simplification tolerance in degrees
           ->  about 0.001 deg = 100 m; 0.00001 deg = 1 m in Europe

    Returns:
         *road_gdf* (GeoPandas DataFrame) : Similar to input gdf, but with hazard data

    """
    #Evaluate the input arguments
    if isinstance(hazard_path,str):
        hazard_path = [hazard_path] #put the path in a list
    elif isinstance(hazard_path,list):
        pass
    else:
        raise ValueError('Invalid input argument')



    #TODO: do this in a seperate function (can be useful for other functions as well)
    # MAP OSM INFRA TYPES TO A SMALLER GROUP OF ROAD_TYPES
    road_gdf = apply_road_mapping(road_gdf)

    #path_settings = load_config()['paths']['settings']
    #road_mapping_path = os.path.join(path_settings, 'OSM_infratype_to_roadtype_mapping.xlsx')
    #road_mapping_dict = import_road_mapping(road_mapping_path, 'Mapping')
    #road_gdf['road_type'] = road_gdf.infra_type.apply(
    #    lambda x: road_mapping_dict[x])  # add a new column 'road_type' with less categories

    # SIMPLIFY ROAD GEOMETRIES
    road_gdf.geometry = road_gdf.geometry.simplify(tolerance=tolerance)
    road_gdf['length'] = road_gdf.geometry.apply(line_length)

    # Take the geometry from the region shapefile
    region_boundary = gpd.read_file(region_path)
    region_boundary.to_crs(epsg=4326, inplace=True)  # convert to WGS84
    geometry = region_boundary['geometry'][0]

    hzd_names = [os.path.split(p)[-1].split('.')[0] for p in hazard_path]
    hzds_data = create_hzd_df(geometry,hazard_path,hzd_names)

    # PERFORM INTERSECTION BETWEEN ROAD SEGMENTS AND HAZARD MAPS
    for iter_, hzd_name in enumerate(hzd_names):

        try:
            hzd_region = hzds_data.loc[hzds_data.hazard == hzd_name]
            hzd_region.reset_index(inplace=True, drop=True)
        except:
            hzd_region == pd.DataFrame(columns=['hazard'])

        if len(hzd_region) == 0:
            road_gdf['length_{}'.format(hzd_name)] = 0
            road_gdf['val_{}'.format(hzd_name)] = 0
            continue

        hzd_reg_sindex = hzd_region.sindex
        tqdm.pandas(desc=hzd_name)
        inb = road_gdf.progress_apply(lambda x: intersect_hazard(x, hzd_reg_sindex, hzd_region), axis=1).copy()
        inb = inb.apply(pd.Series)
        inb.columns = ['geometry', 'val_{}'.format(hzd_name)]
        inb['length_{}'.format(hzd_name)] = inb.geometry.apply(line_length)
        road_gdf[['length_{}'.format(hzd_name), 'val_{}'.format(hzd_name)]] = inb[['length_{}'.format(hzd_name),
                                                                                   'val_{}'.format(hzd_name)]]
        output_path = load_config()['paths']['test_output']
        filename = 'exposure_from_dump.shp'
        road_gdf.to_file(os.path.join(output_path,filename))

        return road_gdf

def add_default_lanes(x, default_lanes_dict):
    """
    Add the default number of lanes if the lane data is missing.

    Arguments:
    *x* (Geopandas Series) -- a row from the region GeoDataFrame with all road segment; needs to have the columns 'NUTS-0' (the country) and 'road_type'
    TODO: applied quickfix here: hardcoded 'NL'as region name
    *default_lanes_dict (OrderedDict) - keys: NUTS-0 country codes; values:
        OrderedDicts with keys: road types and values: default number of lanes

    Returns:
    *x* with the updated number of lanes
    """
    #print(x)
    #print(x.lanes)


    #Note: fetch_roads delivers numpy nans for roads without lane data;
    #      create_network_from_osm_dump() delivers string nans
    #if np.isnan(x.lanes) or  x.lanes == 'nan':
    #TODO: BETTER TO MAKE SURE EACH INPUT SCRIPT DELIVERS THE SAME TYPE OF NAN!!!
    #if x.lanes == 'nan':

    if np.isnan(x.lanes):
        x.lanes = default_lanes_dict['NL'][x['road_type']]
    return x


def load_lane_damage_correction(filename, sheet_name, usecols):
    """
    Loads the maximum damage correction from an Excel file into an ordered dict.

    Argument:
        *filename* (string) - name of the Excel file (should be located in the input_path dir)
        *sheet_name* (string) - name of the excel sheet name
        *usecols* (string) - the columns which have the data (first column should have the road_type keys)

    Returns:
        *lane_corr* (OrderedDict) - keys are road_types; values are dicts with key: lane, value = correction factor
            Use like: lane_corr['motorway'][4] -> 1.25 (i.e. correct max damage by +25%)
    """

    input_path = load_config()['paths']['settings']  # folder containing the Excel_file
    lane_corr_df = pd.read_excel(os.path.join(input_path, filename),
                                 sheet_name=sheet_name, header=3, usecols=usecols, index_col=0)
    odf = OrderedDict()  # initialize OrderedDict
    lane_corr = lane_corr_df.to_dict(orient='index', into=odf)
    return lane_corr


def import_flood_curves(filename, sheet_name, usecols):
    """
    Imports the flood curves from a predefined path

    Arguments:
        *filename* (string) : name of the Excel file (should be located in the input_path folder) e.g. "Costs_curves_Europe.xlsx"
        *sheet_name* (string) : name of the Excel sheet containing the damage curves (e.g. 'curves')
        *usecols* (string) : string with the columns of the Excel sheet you want to import, e.g. "B:AA"

    Returns:
        *OrderedDict* : keys are the names of the damage curves
                        values are scipy interpolators
    """
    from scipy.interpolate import interp1d  # import Scipy interpolator function
    from collections import \
        OrderedDict  # Use an ordered dict so that the damage curves will remain in the order of the Excel sheet

    input_path = load_config()['paths']['settings']  # this is where the other inputs (such as damage curves) are located
    flood_curves = pd.read_excel(os.path.join(input_path, filename),
                                 sheet_name=sheet_name, header=[2], index_col=None,
                                 usecols=usecols)  # removed skip-footer; gave unexpected results
    headers = flood_curves.columns
    curve_name = [0] * int(len(headers) / 2)  # create empty arrays
    interpolators = [0] * int(len(headers) / 2)
    for i in range(0, int(len(headers) / 2)):  # iterate over the damage curves in the Excel file
        curve_name[i] = headers[i * 2]
        curve = flood_curves.iloc[:, 2 * i:2 * i + 2].dropna()
        # curve x-values in the even; and y-values in the uneven columns
        interpolators[i] = interp1d(curve.values[1:, 0], curve.values[1:, 1],
                                    fill_value=(curve.values[1, 1], curve.values[-1, 1]), bounds_error=False)
    return OrderedDict(zip(curve_name, interpolators))


def load_HZ_max_dam(filename, sheet_name, usecols):
    """
    Loads the maximum damages according to Huizinga from an Excel file

    Argument:
        *filename* (string) - name of the Excel file (should be located in the input_path dir)
        *sheet_name* (string) - name of the excel sheet name
        *usecols* (string) - the columns which have the data (first column should have the road_type keys)

    Returns:
        *HZ_max_dam* (OrderedDict) - keys are road_types; values are dicts with key: lane, value = correction factor
            Use like: lane_corr['motorway'][4] -> 1.25 (i.e. correct max damage by +25%)
    """

    input_path = load_config()['paths']['settings']  # folder containing the Excel_file
    lane_corr_df = pd.read_excel(os.path.join(input_path, filename),
                                 sheet_name=sheet_name, header=0, usecols=usecols, index_col=0)
    odf = OrderedDict()  # initialize OrderedDict
    HZ_max_dam = lane_corr_df.to_dict(orient='index', into=odf)
    return HZ_max_dam

def import_damage(file_name, sheet_name, usecols):
    """
    Imports the maximum damage data from an Excel file in the input_path folder

    Arguments:
        *file_name* (string) : name of the Excel file (should be located in the input_path folder)
        *sheet_name* (string) : name of the Excel sheet containing the data
        *usecols* (string) : columns containing the data you want to read, including the column with the road_types e.g. "C:F"

    Returns:
        *dict* (Ordered Dictionary) : An ordered dictionary with a group of damage estimates as keys;
             each value contains another ordered dictionary with as keys the types of roads and as values the damages in Euros
                So you call the output as: dict['Worldbank'] to get a dict with all the damages in WorldBank
                And dict['Worldbank']['motorway'] to get the damage for a motorway according to the worldbank

                #From version 0.7 and higher, this structure maybe does not make much sense, because we use upper and lower bounds

    """
    input_path = load_config()['paths'][
        'settings']  # this is where the other inputs (such as damage curves) are located
    df = pd.read_excel(os.path.join(input_path, file_name),
                       sheet_name=sheet_name, header=[3], usecols=usecols, index_col=0)
    df = df.iloc[df.index.notna(), :]  # Drop the empty cells
    odf = OrderedDict()  # initialize OrderedDict
    return df.to_dict(into=odf)

def apply_lane_damage_correction(lane_damage_correction,road_type,lanes):
    """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
    if lanes < 1: #if smaller than the mapped value -> correct with minimum value
        lanes = 1
    if lanes > 6: #if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
        lanes = 6
    return lane_damage_correction[road_type][lanes]

def apply_HZ_max_dam(max_damages_HZ,road_type,lanes):
    """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
    if lanes < 1: #if smaller than the mapped value -> correct with minimum value
        lanes = 1
    if lanes > 6: #if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
        lanes = 6
    return max_damages_HZ[road_type][lanes]

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
            max_damage = apply_HZ_max_dam(max_damages_HZ, road_type, lanes)  # dict lookup: [road_type][lanes]
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

    # HANDLE EXCEPTIONS BY RETURNING ZERO DAMAGE IN THE APPROPRIATE FORMAT
    # except Exception as e:
    #     errorstring = "Issue with road_loss_estimation, for  x = {} \n exception = {} \n Damages set to zero. \n \n".format(
    #         str(x), e)
    #     log_file = kwargs.get('log_file', None)  # get the name of the log file from the keyword arguments
    #     if log_file is not None:  # write to log file
    #         file = open(log_file, mode="a")
    #         file.write(errorstring)
    #         file.close()
    #     else:  # If no log file is provided, print the string instead
    #         print(errorstring)
    #
    #     for event in events:
    #         if curve_name == "HZ":
    #             x["dam_{}_{}".format(curve_name, event)] = 0
    #         else:
    #             x["dam_{}_{}".format(curve_name, event)] = tuple([0] * 5)  # save empty tuple (0,0,0,0,0)

    return x

def calculate_direct_damage(road_gdf):
    """
    Calculates the direct damage for all road segments with exposure data using a depth-damage curve

    Arguments:
        *road_gdf* (GeoPandas DataFrame) :

    Returns:
        *road_gdf* () :


    """

    #todo: currently reads from the OSdaMage pickle containing European Road statistics (and takes values for 'NL')
    #whereas it should read from an Excel file instead.
    lane_file = os.path.join(load_config()['paths']['settings'],
                            'default_lanes_temp.pkl') # import the pickle containing the default lane data

    with open(lane_file, 'rb') as handle:
        default_lanes_dict = pickle.load(handle)

    road_gdf = road_gdf.apply(lambda x: add_default_lanes(x, default_lanes_dict),
                  axis=1).copy()  # apply the add_default_lanes function
    # This should also work with a default dict, because now seems to raise an exception also when it is an unused road type

    # LOAD THE DICT REQUIRED FOR CORRECTING THE MAXIMUM DAMAGE BASED ON THE NUMBER OF LANES
    lane_damage_correction = load_lane_damage_correction('OSdaMage_functions.xlsx', "Max_damages", "G:M")
    # actual correction is done within the road_loss_estimation function

    dict_max_damages = import_damage('OSdaMage_functions.xlsx', "Max_damages", usecols="C:E")
    max_damages_HZ = load_HZ_max_dam('OSdaMage_functions.xlsx', "Huizinga_max_dam", "A:G")

    # LOAD THE DAMAGE FUNCTIONS
    interpolators = import_flood_curves(filename = 'OSdaMage_functions.xlsx', sheet_name='All_curves', usecols="B:O")

    # PERFORM LOSS CALCULATION FOR ALL ROAD SEGMENTS
    val_cols = [x for x in list(road_gdf.columns) if 'val' in x]
    # Remove all rows from the dataframe containing roads that don't intersect with floods
    df = road_gdf.loc[~(road_gdf[val_cols] == 0).all(axis=1)]

    hzd_names = [i.split('val_')[1] for i in val_cols]

    #TODO: DIT LIJKT ME EEN BEETJE OMSLACHTIG, KAN MISSCHIEN NOG WAT OVERZICHTELIJKER
    for curve_name in interpolators:
        interpolator = interpolators[curve_name]  # select the right interpolator
        df = df.progress_apply(
            lambda x: road_loss_estimation(x, interpolator, hzd_names, dict_max_damages, max_damages_HZ, curve_name,
                                           lane_damage_correction), axis=1)

    output_path = load_config()['paths']['test_output']
    filename = 'damage.shp'
    #df.to_file(os.path.join(output_path, filename))
    #Does not yet work, because the results are stored in tuples

    return df



if __name__ =='__main__':
    road_gdf, road_gdf_graph = generate_damage_input(0.001)
    road_gdf.rename(columns={'highway': 'infra_type'}, inplace=True)
    assert 'infra_type' in road_gdf.columns

    #PLEASE NOTE THAT THE LINE BELOW CRIES FOR AN OBJECT-BASED APPROACH (OOP) :)
    #OOP would make it:
    #road_gdf.apply_road_mapping()
    road_gdf = apply_road_mapping(road_gdf)  # Map the infra_types (many) to road_types (a few)

    #TODO: THIS SHOULD NOT BE DONE HERE, BUT ALREADY IN THE GENERATE_DAMAGE_INPUT
    road_gdf.loc[road_gdf.lanes == 'nan','lanes'] = np.nan #replace string nans with numpy nans
    road_gdf.lanes = road_gdf.lanes.astype('float') #convert strings to floats (not int, because int cant have nan)

    #LOAD SOME SAMPLE DATA
    #LOAD SHAPEFILE TO CROP THE HAZARD MAP
    filename = 'NUTS332.shp'
    region_path = os.path.join(load_config()['paths']['test_area_of_interest'],filename)

    hzd_path = load_config()['paths']['test_hazard']
    hzd_path = os.path.join(hzd_path,'efas_rp500_wgs84.tif')

    road_gdf_exposure = add_hazard_data_to_road_network(road_gdf,region_path,hzd_path)

    road_gdf_damage = calculate_direct_damage(road_gdf)

    print(road_gdf_damage.head)
