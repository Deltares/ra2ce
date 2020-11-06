# create graph from OSM
import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)

from shapely.wkb import loads
import ogr
import networkx as nx
import osmnx
import fiona
from shapely.geometry import shape
import geopandas as gpd
from pathlib import Path
from numpy import object as np_object
import time
import filecmp
from utils import load_config
from shapely.geometry import LineString, Point
from decimal import Decimal
import numpy as np
import logging
from networkx import set_edge_attributes

LOG_FILENAME = './logs/log_create_network_from_osm_dump.log'
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

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

def convert_osm(osm_convert_path, pbf, o5m):
    """
    Convers an osm PBF file to o5m
    """

    command = '""{}"  "{}" --complete-ways --drop-broken-refs -o="{}""'.format(osm_convert_path, pbf, o5m)
    os.system(command)


def filter_osm(osm_filter_path, o5m, filtered_o5m, tags=None):

    """Filters an o5m OSM file to only motorways, trunks, primary and secondary roads
    """
    if tags is None:
        tags = ['motorway', 'motorway_link', 'primary', 'primary_link',
                'secondary', 'secondary_link', 'trunk', 'trunk_link']

    command = '""{}"  "{}" --keep="highway={}" > "{}""'.format(osm_filter_path, o5m, " =".join(tags), filtered_o5m)
    os.system(command)


def graph_to_gdf(G):
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

    return edges, nodes


# def create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe, **kwargs):
#     """
#     Filters and generates a graph from an osm.pbf file
#     Args:
#         pbf: path object for .pbf file
#         o5m: path for o5m file function object for filtering infrastructure from osm pbf file
#         **kwargs: all kwargs to osmnx.graph_from_file method. Use simplify=False and retain_all=True to preserve max
#         complexity when generating graph
#
#     Returns:
#         G: graph object
#         nodes: geodataframe representing graph nodes
#         edges: geodataframe representing graph edges
#     """
#
#     filter_osm(osm_filter_exe, o5m, o5m_filtered)
#     G = osmnx.graph_from_file(o5m_filtered, **kwargs)
#     G = G.to_undirected()
#     edges, nodes = graph_to_gdf(G)
#
#     return G, edges, nodes


def compare_files(ref_files, test_files):
    for ref_file, test_file in zip(ref_files, test_files):
        if str(test_file).endswith('nodes.geojson'):
            pass
        else:
            assert filecmp.cmp(ref_file, test_file), '{} and {} do are not the same'.format(str(ref_file), str(test_file))
        os.remove(test_file)

def cut(line, distance):
    """Cuts a line in two at a distance from its starting point

    :param line: a shapely geometry line object (shapely.geometry.linestring.LineString)
    :param distance: distance from starting point of linestring (float)
    :return: a list containing two shapely linestring objects.
    """

    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def check_divisibility(dividend, divisor):
    """Checks if the dividend is a multiple of the divisor and outputs a
    boolean value

    :param dividend: the number which is divided (float)
    :param divisor: the number which divides (float)
    :return: bool: True if the dividend is a multiple of the divisor, False if not (bool)
    """

    dividend = Decimal(str(dividend))
    divisor = Decimal(str(divisor))
    remainder = dividend % divisor

    if remainder == Decimal('0'):
        is_multiple = True
        return is_multiple
    else:
        is_multiple = False
        return is_multiple

def number_of_segments(linestring, split_length):
    """returns the integer number of segments which will result from chopping up a linestring with split_length

    :param linestring: a shapely linestring object. (shapely.geometry.multilinestring.MultiLineString)
    :param split_length: the length by which to divide the linestring object. (float)
    :return: n: integer number of segments which will result from splitting linestring with split_length. (int)
    """

    divisible = check_divisibility(linestring.length, split_length)
    if divisible:
        n = int(linestring.length/split_length)
    else:
        n = int(linestring.length/split_length)+1
    return n

def split_linestring(linestring, split_length):
    """cuts a linestring in equivalent segments of length split_length

    :param linestring: linestring object. (shapely.geometry.linestring.LineString)
    :param split_length: length by which to split the linestring into equal segments. (float)
    :return: result_list: list of linestring objects all having the same length. (list)
    """

    n_segments = number_of_segments(linestring, split_length)
    if n_segments != 1:
        result_list = [None]*n_segments
        current_right_linestring = linestring

        for i in range(0, n_segments-1):
            r = cut(current_right_linestring, split_length)
            current_left_linestring = r[0]
            current_right_linestring = r[1]
            result_list[i] = current_left_linestring
            result_list[i+1] = current_right_linestring
    else:
        result_list = [linestring]

    return result_list


def cut_gdf(gdf, length):
    """
    Cuts every linestring or multilinestring feature in a gdf to equal length segments. Assumes only linestrings for now.
    """

    columns = gdf.columns
    data = {}
    data['splt_id'] = []

    for column in columns:
        data[column] = []

    count = 0
    for i, row in gdf.iterrows():
        geom = row['geometry']
        assert type(geom)==LineString
        linestrings = split_linestring(geom, length)

        for j, linestring in enumerate(linestrings):
            for key, value in row.items():
                if key=='geometry':
                    data[key].append(linestring)
                else:
                    data[key].append(value)
            data['splt_id'].append(count)
            count += 1

    return gpd.GeoDataFrame(data)


def test_bookkeeping():
    root = Path(__file__).parents[2]
    test_output_dir = Path(load_config()['paths']['test_output'])
    test_input_osm_dumps_dir = Path(load_config()['paths']['test_OSM_dumps'])

    osm_filter_exe = root / 'osmfilter.exe'
    osm_convert_exe = root / 'osmconvert64.exe'
    pbf = test_input_osm_dumps_dir / r"NL332.osm.pbf"
    o5m = test_output_dir / r"NL332.o5m"
    o5m_filtered = test_output_dir / 'NL332_filtered.o5m'

    convert_osm(osm_convert_exe, pbf, o5m)
    filter_osm(osm_filter_exe, o5m, o5m_filtered)

    G_complex, edges_complex, nodes_complex = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe,
                                                                           simplify=False, retain_all=True)

    edges_complex['complex_graph_id'] = edges_complex.index

    return cut_gdf(edges_complex, 0.001)

def test_cut_gdf():
    test_output_dir = Path(load_config()['paths']['test_output'])
    shapefile =  test_output_dir / 'NL332_edges_simplified.shp'
    gdf = gpd.read_file(shapefile)
    gdf = cut_gdf(gdf, 0.006)
    gdf.to_file(test_output_dir / 'NL221_edges_simplified_split.shp')
    print('done')


def test_create_network_from_osm_dump():
    # run function
    root = Path(__file__).parents[2]
    test_output_dir = Path(load_config()['paths']['test_output'])
    test_input_osm_dumps_dir = Path(load_config()['paths']['test_OSM_dumps'])

    osm_filter_exe = root / 'osmfilter.exe'
    osm_convert_exe = root / 'osmconvert64.exe'
    pbf = test_input_osm_dumps_dir / r"NL332.osm.pbf"
    o5m = test_output_dir / r"NL332.o5m"
    o5m_filtered = test_output_dir / 'NL332_filtered.o5m'

    convert_osm(osm_convert_exe, pbf, o5m)
    filter_osm(osm_filter_exe, o5m,  o5m_filtered)
    G, edges, nodes = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe, simplify=True, retain_all=True)

    edges.to_file(test_output_dir / 'NL332_edges_simplified_retained.shp')
    nodes.to_file(test_output_dir / 'NL332_nodes_simplified_retained.shp')

    G, edges, nodes = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe, simplify=False, retain_all=False)

    edges.to_file(test_output_dir / 'NL332_edges.shp')
    nodes.to_file(test_output_dir / 'NL332_nodes.shp')

    G, edges, nodes = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe, simplify=False, retain_all=True)

    edges.to_file(test_output_dir / 'NL332_edges_retained.shp')
    nodes.to_file(test_output_dir / 'NL332_nodes_retained.shp')

    G, edges, nodes = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe, simplify=True, retain_all=False)

    edges.to_file(test_output_dir / 'NL332_edges_simplified.shp')
    nodes.to_file(test_output_dir / 'NL332_nodes_simplified.shp')

def generate_damage_input(split_length):
    root = Path(__file__).parents[2]
    test_output_dir = Path(load_config()['paths']['test_output'])
    test_input_osm_dumps_dir = Path(load_config()['paths']['test_OSM_dumps'])

    osm_filter_exe = root / 'osmfilter.exe'
    osm_convert_exe = root / 'osmconvert64.exe'
    pbf = test_input_osm_dumps_dir / r"NL332.osm.pbf"
    o5m = test_output_dir / r"NL332.o5m"
    o5m_filtered = test_output_dir / 'NL332_filtered.o5m'

    convert_osm(osm_convert_exe, pbf, o5m)
    filter_osm(osm_filter_exe, o5m, o5m_filtered)

    G_complex, edges_complex, nodes_complex = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe,
                                                                           simplify=False, retain_all=True)

    G_simple, edges_simple, nodes_simple = create_network_from_osm_dump(o5m, o5m_filtered, osm_filter_exe,
                                                                        simplify=True, retain_all=True)

    edges_simple['grph_id'] = edges_simple.index
    edges_complex['gdf_id'] = edges_complex.index
    edges_complex['grph_id'] = -9999
    edges_complex_split = cut_gdf(edges_complex, split_length)

    assert edges_complex_split['splt_id'].is_unique

    for i, row in edges_simple.iterrows():
        osmids = eval(row['osmid'])
        if isinstance(osmids, list):
            for osmid in osmids:
                edges_complex_split.loc[edges_complex_split['osmid']==osmid, 'grph_id'] = row['grph_id']
        else:
            edges_complex_split.loc[edges_complex_split['osmid'] == int(osmids), 'grph_id'] = row['grph_id']

    return edges_complex_split, edges_simple

def graphs_from_o5m(o5m_path,AllOutput=None,bidirectional=False, simplify=True,
                    retain_all=False, save_shapes=False):
    """
    Generates a complex and simplified graph from an o5m file.
    This function is based on the osmnx.graph_from_file function.

    Arguments:
        *o5m_path* (Pathlib Path object) : path to the o5m file (probably you want to use the filtered one!)
        *simplify* (Boolean) : should the graph be simplified?
        *save_shapes* (Boolean) : save the graphs as geodataframes
        *output_path* (Pathlib Path object) : the path where the outputs are to be saved

    Returns:
        *G_complex* (Graph object) : unsimplified graph
        *G_simple* (Graph object) : simplified graph
    """
    from osmnx.utils import overpass_json_from_file
    from osmnx.core import create_graph
    from osmnx.simplify import simplify_graph

    # transmogrify file of OSM XML data into JSON
    filename = o5m_path
    response_jsons = [overpass_json_from_file(filename)]

    # create graph using this response JSON
    G_complex = create_graph(response_jsons, bidirectional=bidirectional,
                     retain_all=retain_all, name='unnamed')

    G_complex = graph_create_unique_ids(G_complex, 'G_complex_fid')

    print('graphs_from_o5m() returning graph with {:,} nodes and {:,} edges'.format(len(list(G_complex.nodes())),
                                                                                    len(list(G_complex.edges()))))
    # simplify the graph topology as the last step.
    if simplify:
        G_simple = simplify_graph(G_complex)
        G_simple = graph_create_unique_ids(G_simple, 'G_simple_fid')
        print('graphs_from_o5m() returning graph with {:,} nodes and {:,} edges'.format(len(list(G_simple.nodes())),
                                                                                        len(list(G_simple.edges()))))
    else:
        G_simple = None
        print('Did not create a simplified version of the graph')


    if save_shapes:
        graph_to_shp(G_complex, Path(AllOutput).joinpath('{}_edges.shp'.format('G_complex')),
                 Path(AllOutput).joinpath('{}_nodes.shp'.format('G_complex')))

        if simplify:
            graph_to_shp(G_simple, Path(AllOutput).joinpath('{}_edges.shp'.format('G_simple')),
                 Path(AllOutput).joinpath('{}_nodes.shp'.format('G_simple')))

    return G_complex,G_simple

def graph_create_unique_ids(graph,new_id_name):
    # Check if new_id_name exists and if unique
    #else  create new_id_name
    # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
    #
    # else:
        i = 0
        for u, v, k in graph.edges(keys=True):
            graph[u][v][k][new_id_name] = i
            i += 1
        print(
            "Added a new unique identifier field {}.".format(
                new_id_name))
        return graph
    # else:
    #     return graph, new_id_name

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

    # The nodes should have a geometry attribute (perhaps on top of the x and y attributes)
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

def from_dump_tool_workflow(path_to_pbf,road_types):
    """
    Example workflow for use in the tool version of RA2CE

    Arguments:
        *path_to_pbf* (Path) : Path to the osm_dump from which the road network is to be fetched
        *road_types* (list of strings) : The road types to fetch from the dump e.g. ['motorway', 'motorway_link']

    Returns:
        G_simple (Graph) : Simplified graph (for use in the indirect analyses)
        G_complex_edges (GeoDataFrame : Complex graph (for use in the direct analyses)
    """
    ra2ce_main_path = Path(__file__).parents[1]
    osm_convert_exe = ra2ce_main_path / 'osmconvert64.exe'
    osm_filter_exe = ra2ce_main_path / 'osmfilter.exe'
    assert osm_convert_exe.exists() and osm_filter_exe.exists()

    # Prepare the making of a new o5m in the same folder as the pbf
    o5m_path = path_to_pbf.parents[0] / '{}.o5m'.format(path_to_pbf.stem.split('.')[0])
    o5m_filtered_path = path_to_pbf.parents[0] / '{}_filtered.o5m'.format(path_to_pbf.stem.split('.')[0])

    # CONVERT FROM PBF TO O5M
    if not o5m_path.exists():
        assert not o5m_filtered_path.exists()
        print('Start conversion from pbf to o5m')
        convert_osm(osm_convert_exe, path_to_pbf, o5m_path)
        print('Converted osm.pbf to o5m, created: {}'.format(o5m_path))
    else:
        print('O5m path already exists, uses the existing one!: {}'.format(o5m_path))

    if not o5m_filtered_path.exists():
        print('Start filtering')
        filter_osm(osm_filter_exe, o5m_path, o5m_filtered_path,tags=road_types)
        print('Filtering finished')
    else:
        print('filtered o5m path already exists: {}'.format(o5m_filtered_path))

    assert o5m_path.exists() and o5m_filtered_path.exists()

    G_complex, G_simple = graphs_from_o5m(o5m_filtered_path, AllOutput=None, bidirectional=False, simplify=True,
                    retain_all=False, save_shapes=False)

    #CONVERT GRAPHS TO GEODATAFRAMES
    print('Start converting the graphs to geodataframes')
    edges_complex, nodes_complex = graph_to_gdf(G_complex)
    edges_simple, nodes_simple = graph_to_gdf(G_simple)
    print('Finished converting the graphs to geodataframes')

    #return G_complex, G_simple,edges_simple,nodes_simple,edges_complex,nodes_complex
    return G_simple, edges_complex


if __name__ == '__main__':

    #Uses the from_tool_workflow as a test procedure; that works well :)
    pbf_path = Path(__file__).parents[1] / 'test/input/OSM_dumps/NL332.osm.pbf'
    tags = ['motorway', 'motorway_link', 'primary', 'primary_link',
                'secondary', 'secondary_link', 'trunk', 'trunk_link']
    G_simple, G_complex = from_dump_tool_workflow(pbf_path,road_types=tags)
    print('finished')

    #TODO: THE CUT_GDF IS NOT YET TESTED
