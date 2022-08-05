"""
Utils to proprocess OpenStreetMap data.

Contains the preprocessing functions required for running the OSdaMage model. The functions are called from a Jupyter Notebook 'Preproc_split_OSM.ipynb'

This code is maintained on a GitHub repository: github.com/keesvanginkel/OSdaMage

@author: Elco Koks and Kees van ginkel
"""

import geopandas as gpd
import logging
import matplotlib.pyplot as plt
import numpy as np
import os 
import pandas as pd
from shapely.geometry import MultiPolygon
from pathlib import Path

#import same ra2ce functionality
from ra2ce.utils import get_root_path, load_config


def from_shapefile_to_poly(shapefile, out_path,outname=None):
    
    """
    This function will create the .poly files from an input shapefile.
    If the shapefile contains multiple polygons, this function creates a seperate .polygon file for each region
    .poly files can then be used to extract data from the openstreetmap files.
    
    This function is adapted from the OSMPoly function in QGIS, and Elco Koks GMTRA model.
    
    Arguments:
        *shapefile* (string/Pathlib Path) : path to the shapefile
        *out_path* (string/Pathlib Path): path to the directory where the .poly files should be written
        *outname* (string) : optional prefix to add to outfile name
    
    Returns:
        .poly file for each region, in a new dir in the working directory (in the CRS of te input file)
    """   
    shapefile = str(shapefile)
    out_path = str(out_path)
    shapefile_GDF = gpd.read_file(shapefile)

    num = 0
    # iterate over the seperate polygons in the shapefile
    for f in shapefile_GDF.iterrows():
        f = f[1]
        num = num + 1
        geom=f.geometry

        try:
            # this will create a list of the different subpolygons
            if geom.geom_type == 'MultiPolygon':
                polygons = geom

            # the list will be length 1 if it is just one polygon
            elif geom.geom_type == 'Polygon':
                polygons = [geom]

            # define the name of the output file
            id_name = str(f.name)

            # start writing the .poly file
            f = open(out_path + "/" + outname + id_name +'.poly', 'w')
            f.write(id_name + "\n")

            i = 0

            # loop over the different polygons, get their exterior and write the 
            # coordinates of the ring to the .poly file
            for polygon in polygons:

                polygon = np.array(polygon.exterior)

                j = 0
                f.write(str(i) + "\n")

                for ring in polygon:
                    j = j + 1
                    f.write("    " + str(ring[0]) + "     " + str(ring[1]) +"\n")

                i = i + 1
                # close the ring of one subpolygon if done
                f.write("END" +"\n")

            # close the file when done
            f.write("END" +"\n")
            f.close()
        except Exception as e:
            print("Exception {}".format(e))

if __name__ == "__main__":
    ### Used for a Zuid-Holland test.
    # Find the network.ini and analysis.ini files
    data_folder = Path(r'D:\Python\ra2ce\data\1000_zuid_holland')
    network_ini = data_folder / 'network.ini'
    analyses_ini = None

    root_path = get_root_path(network_ini, analyses_ini)

    #if network_ini:
    #    config_network = load_config(root_path, config_path=network_ini)

    #############################################################################
    #STEP 1: Convert shapefile to .poly file(s)
    shapefile = data_folder / 'input' / 'zuid_holland_epsg4326_wgs84.shp'
    assert shapefile.exists()

    out_path = data_folder / 'input'

    from_shapefile_to_poly(shapefile,out_path,'zh_') #Returns

    #############################################################################
    #STEP 2: Use .poly file to cut down the osm.pbf
    input_osm_pbf = data_folder / 'input' / 'netherlands.osm.pbf'

    osm_convert_exe = root_path.parents[0] / 'ra2ce' / 'executables'/ 'osmconvert64.exe'
    polyfile = data_folder / 'input' / 'zh_0.poly'
    outfile = data_folder / 'input' / (polyfile.stem + '.o5m')
    assert osm_convert_exe.exists()
    assert polyfile.exists()

    #For documentation on how the executable works, see this wiki: https://wiki.openstreetmap.org/wiki/Osmconvert
    os.system('{}  {} -B={} --complete-ways --drop-broken-refs --hash-memory=10000 --out-o5m -o={}'.format(
        str(osm_convert_exe), str(input_osm_pbf), str(polyfile), str(outfile)))