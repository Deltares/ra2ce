# create graph from OSM
import os as os
import geopandas as gpd
from shapely.wkb import loads
import ogr
import numpy as np

import time

def fetch_roads(osm_data, region, **kwargs):
    """
    Function to extract all roads from OpenStreetMap for the specified region.

    Arguments:
        *osm_data* (string) -- string of data path where the OSM extracts (.osm.pbf) are located.
        *region* (string) -- NUTS3 code of region to consider.

        *log_file* (string) OPTIONAL -- string of data path where the log details should be written to

    Returns:
        *Geodataframe* -- Geopandas dataframe with all roads in the specified **region**.

    """

    ## LOAD FILE
    osm_path = os.path.join(osm_data, '{}.osm.pbf'.format(region))
    driver = ogr.GetDriverByName('OSM')
    data = driver.Open(osm_path)

    ## PERFORM SQL QUERY
    sql_lyr = data.ExecuteSQL("SELECT osm_id,highway,other_tags FROM lines WHERE highway IS NOT NULL")

    log_file = kwargs.get('log_file', None)  # if no log_file is provided when calling the function, no log will be made

    if log_file is not None:  # write to log file
        file = open(log_file, mode="a")
        file.write("\n\nRunning fetch_roads for region: {} at time: {}\n".format(region, time.strftime(
            "%a, %d %b %Y %H:%M:%S +0000", time.gmtime())))
        file.close()

    ## EXTRACT ROADS
    roads = []
    for feature in sql_lyr:  # Loop over all highway features
        if feature.GetField('highway') is not None:
            osm_id = feature.GetField('osm_id')
            shapely_geo = loads(feature.geometry().ExportToWkb())  # changed on 14/10/2019
            if shapely_geo is None:
                continue
            highway = feature.GetField('highway')
            try:
                other_tags = feature.GetField('other_tags')
                dct = OSM_dict_from_other_tags(other_tags)  # convert the other_tags string to a dict

                if 'lanes' in dct:  # other metadata can be drawn similarly
                    try:
                        # lanes = int(dct['lanes'])
                        lanes = int(round(float(dct['lanes']), 0))
                        # Cannot directly convert a float that is saved as a string to an integer;
                        # therefore: first integer to float; then road float, then float to integer
                    except:
                        if log_file is not None:  # write to log file
                            file = open(log_file, mode="a")
                            file.write(
                                "\nConverting # lanes to integer did not work for region: {} OSM ID: {} with other tags: {}".format(
                                    region, osm_id, other_tags))
                            file.close()
                        lanes = np.NaN  # added on 20/11/2019 to fix problem with UKH35
                else:
                    lanes = np.NaN

                if 'bridge' in dct:  # other metadata can be drawn similarly
                    bridge = dct['bridge']
                else:
                    bridge = np.NaN

                if 'lit' in dct:
                    lit = dct['lit']
                else:
                    lit = np.NaN

            except Exception as e:
                if log_file is not None:  # write to log file
                    file = open(log_file, mode="a")
                    file.write(
                        "\nException occured when reading metadata from 'other_tags', region: {}  OSM ID: {}, Exception = {}\n".format(
                            region, osm_id, e))
                    file.close()
                lanes = np.NaN
                bridge = np.NaN
                lit = np.NaN

            # roads.append([osm_id,highway,shapely_geo,lanes,bridge,other_tags]) #include other_tags to see all available metata
            roads.append([osm_id, highway, shapely_geo, lanes, bridge,
                          lit])  # ... but better just don't: it could give extra errors...
    ## SAVE TO GEODATAFRAME
    if len(roads) > 0:
        return gpd.GeoDataFrame(roads,columns=['osm_id','infra_type','geometry','lanes','bridge','lit'],crs={'init': 'epsg:4326'})
    else:
        print('No roads in {}'.format(region))
        if log_file is not None:
            file = open(log_file, mode="a")
            file.write('No roads in {}'.format(region))
            file.close()

if __name__=='__main__':
    start = time.time()
    osm_dump_path = os.path.join('..', '..', "sample_data")

    region = 'NL332'
    print('Checking for region {}'.format(region))
    print("File exists? ", os.path.exists(osm_dump_path))

    output = fetch_roads(osm_dump_path,region)
    print(output)

    interesting = ['motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link']
    selection = output[output['infra_type'].isin(interesting)]

    end = time.time()
    print("Runtime: ",end-start,"seconds")

