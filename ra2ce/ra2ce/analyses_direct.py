# Direct analyses
from collections import defaultdict
import pickle
import pandas as pd
import geopandas as gpd
import os
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


            # this is specific to this calculation: change to WGS84 (anticipating intersect with OSM)
            #gdf.crs = {'init': 'epsg:28992'}
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

def add_hazard_data_to_road_network():
    """
    Adds the hazard data to the road network, i.e. creates an exposure map

    Arguments

    """

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

    # SIMPLIFY ROAD GEOMETRIES
    road_gdf.geometry = road_gdf.geometry.simplify(tolerance=tolerance)
    road_gdf['length'] = road_gdf.geometry.apply(line_length)

    # LOAD SHAPEFILE TO CROP THE HAZARD MAP
    regional_shapefile = load_config()['paths']['test_area_of_interest']
    filename = 'NUTS332.shp'
    complete_path = os.path.join(regional_shapefile,filename)
    print(complete_path)
    print(os.path.exists(complete_path))
    region_boundary = gpd.read_file(complete_path)
    region_boundary
    region_boundary.to_crs(epsg=4326,inplace=True) #convert to WGS84 #region_boundary.to_crs(epsg=4326,inplace=True) #convert to WGS84
    #region_boundary.to_crs(epsg=28992, inplace=True)  # convert to Amersfoort / RD new
    #region_boundary.to_crs(epsg=3035,inplace=True)
    region_boundary.plot()
    plt.show()

    geometry = region_boundary['geometry'][0]



    hzd_path = load_config()['paths']['test_hazard']
    #hzd_list = natsorted([os.path.join(hzd_path, x) for x in os.listdir(hzd_path) if x.endswith(".tif")])
    #hzd_names = ['a','b']

    hzd_list = [os.path.join(hzd_path,'Lizard_13942_wgs84.tif')]
    hzd_names = ['Lizard_13942']

    hzds_data = create_hzd_df(geometry,hzd_list,hzd_names)
    hzds_data.to_file('hzds_data_vectorized.shp')

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

    print(road_gdf)
    road_gdf.to_file('anothertest4.shp')
    print('einde')
