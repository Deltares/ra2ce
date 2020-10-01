# Direct analyses
from collections import defaultdict
import pickle
import pandas as pd
import geopandas as gpd
import os
from boltons.iterutils import pairwise
from geopy.distance import vincenty

from utils import load_config



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

if __name__ == '__main__':

    #UDI:
    tolerance = 0.00005 # Tolerance for the simplification of linestrings, in degrees (WGS84)
    #### #about 0.001 = 100 m; 0.00001 = 1 m ####


    #LOAD SOME SAMPLE DATA
    folder = load_config()['paths']['test_temp']
    path = os.path.join(folder,'OSD_create_network_from_dump_temp.pkl')
    pickle_in = open(path,"rb")
    road_gdf = pickle.load(pickle_in)
    pickle_in.close()

    #MAP OSM INFRA TYPES TO A SMALLER GROUP OF ROAD_TYPES
    path_settings = load_config()['paths']['settings']
    road_mapping_path = os.path.join(path_settings,'OSM_infratype_to_roadtype_mapping.xlsx')
    road_mapping_dict = import_road_mapping(road_mapping_path,'Mapping')
    road_gdf['road_type'] = road_gdf.infra_type.apply(
        lambda x: road_mapping_dict[x])  # add a new column 'road_type' with less categories

    # OPTIONALLY: CALCULATE LINE LENGTHS (IF THIS IS NOT ALREADY DONE!!!)
    road_gdf['length'] = road_gdf.geometry.apply(line_length)
    # SIMPLIFY ROAD GEOMETRIES
    road_gdf.geometry = road_gdf.geometry.simplify(tolerance=tolerance)

    # LOAD SHAPEFILE TO CROP THE HAZARD MAP
    regional_shapefile = load_config()['paths']['test_network_shp']
    filename = 'NL332.shp'
    complete_path = os.path.join(regional_shapefile,filename)
    print(os.path.exists(complete_path))
    NUTS_regions = gpd.read_file(os.path.join(input_path, load_config()['filenames']['NUTS3-shape']))





    print('einde')
