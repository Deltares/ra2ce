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
from pathlib import Path
from create_network_from_osm_dump import generate_damage_input


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
    path_settings = load_config()['paths']['settings']
    road_mapping_path = os.path.join(path_settings, 'OSM_infratype_to_roadtype_mapping.xlsx')
    road_mapping_dict = import_road_mapping(road_mapping_path, 'Mapping')
    road_gdf['road_type'] = road_gdf.infra_type.apply(
        lambda x: road_mapping_dict[x])  # add a new column 'road_type' with less categories

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


if __name__ =='__main__':
    road_gdf, road_gdf_graph = generate_damage_input(0.001)
    road_gdf.rename(columns={'highway': 'infra_type'}, inplace=True)
    assert 'infra_type' in road_gdf.columns
    #LOAD SOME SAMPLE DATA
    # LOAD SHAPEFILE TO CROP THE HAZARD MAP
    filename = 'NUTS332.shp'
    region_path = os.path.join(load_config()['paths']['test_area_of_interest'],filename)

    hzd_path = load_config()['paths']['test_hazard']
    hzd_path = os.path.join(hzd_path,'efas_rp500_wgs84.tif')

    road_gdf = add_hazard_data_to_road_network(road_gdf,region_path,hzd_path)
    print(road_gdf.head())
