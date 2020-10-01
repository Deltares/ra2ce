# create graph from OSM
import os as os
import geopandas as gpd
from shapely.wkb import loads
import ogr
import numpy as np
import networkx as nx
import osmnx
import fiona
from shapely.geometry import shape
import geopandas as gpd
from pathlib import Path
import os
import sys
from numpy import object as np_object
import time

### Overrule the OSMNX default settings to get the additional metadata such as street lighting (lit)
osmnx.config(log_console=True, use_cache=True, useful_tags_path = osmnx.settings.useful_tags_path + ['lit'])
sys.setrecursionlimit(10**5)

def fetch_roads(region, osm_pbf_path, **kwargs):
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

    driver = ogr.GetDriverByName('OSM')
    data = driver.Open(osm_pbf_path)

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

if __name__=='__main__':
    root = Path(__file__).parents[2]

    osm_filter_path = root / 'osmfilter.exe'
    osm_convert_path = root / 'osmconvert64.exe'
    pbf = root / r"sample_data/NL332.osm.pbf"
    poly = root / r"sample_data/NL332.poly"
    o5m = root / 'sample_data/NL332.o5m'
    region = 'NL332'
    command = '""{}"  "{}" --complete-ways -o="{}""'.format(osm_convert_path, pbf, o5m)
    osm_dump_path = "sample_data"

    os.system(command)
    filter_osm(osm_filter_path, o5m,  root / 'sample_data/NL332_filtered.o5m')
    G = osmnx.graph_from_file(root / 'sample_data/NL332_filtered.o5m', simplify=True, retain_all=True)
    G = G.to_undirected()
    #G = graph_from_osm(str(root / 'sample_data/NL332_filtered.o5m'), multidirectional=False)
    nodes,edges = osmnx.graph_to_gdfs(G)
    graph_to_shp(G,root / 'test_results/edges.shp',root / 'test_results/nodes.shp')
    output = fetch_roads(region, str(pbf))
    interesting = ['motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link']
    selection = output[output['infra_type'].isin(interesting)]
    selection.to_file(root / 'test_results/OSD_create_network_from_dump_temp.shp')
