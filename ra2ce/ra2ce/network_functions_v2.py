# -*- coding: utf-8 -*-
"""
Created on Thu May 16 17:09:19 2019

@author: Frederique de Groen

Part of a general tool for criticality analysis of networks.

"""
''' MODULES '''
import networkx as nx
import osmnx
import fiona
from shapely.geometry import shape
import geopandas as gpd
from pathlib import Path
import os
import sys
import time

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

def graph_from_osm(osm_files, multidirectional=False):
    """
    Takes in a list of osmnx compatible files as strings, creates individual graph from each file then combines all
    graphs using the compose_all function from networkx. Most suited for cases where each file represents part of the
    same greater network.

    Arguments:
        list_of_osm_files [list or str]: list of osm xml filenames as strings, see osmnx documentation for compatible file
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

if __name__=='__main__':
    begin_time = time.time()
    osm_filter_path = 'osmfilter.exe'
    osm_convert_path = 'osmconvert64.exe'
    pbf = r"sample_data/NL332.osm.pbf"
    poly = r"sample_data/NL332.poly"
    o5m = 'sample_data/NL332.o5m'

    command = '""{}"  "{}" --complete-ways -o="{}""'.format(osm_convert_path, pbf, o5m)
    os.system(command)
    filter_osm(osm_filter_path, o5m,  'sample_data/NL332_filtered.o5m')

    # create a graph
    G = graph_from_osm('sample_data/NL332_filtered.o5m', multidirectional=False)

    print(time.time() - begin_time)
