# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

# external modules
import networkx as nx
import osmnx
from numpy import object as np_object
from shapely.geometry import shape
import geojson
import logging
import geopandas as gpd
from shapely.geometry import Point, LineString
import pickle
from osmnx.simplification import simplify_graph


class Network:
    def __init__(self, config):
        self.config = config
        self.save_shp = True if config['network']['save_shp'] == 'true' else False
        self.save_csv = True if config['network']['save_csv'] == 'true' else False

    def network_shp(self):
        """Creates a network from a shapefile."""
        return

    def network_osm_pbf(self):
        """Creates a network from an OSM PBF file."""
        return

    def network_osm_download(self):
        """Creates a network from a polygon by downloading via the OSM API in the extent of the polygon.

        Arguments:
            *InputDict* (Path) with
            PathShp [string]: path to shapefile (polygon) used to download from OSMnx the roads in that polygon
            NetworkType [string]: one of the network types from OSM, e.g. drive, drive_service, walk, bike, all
            RoadTypes [string]: formatted like "motorway|primary", one or multiple road types from OSM (highway)
            undirected is True, unless specified as False
            simplify graph is True, unless specified as False
            save_shapes is False, unless you would like to save shapes of both graphs

        Returns:
            G_simple (Graph) : Simplified graph (for use in the indirect analyses)
            G_complex_edges (GeoDataFrame : Complex graph (for use in the direct analyses)
        """
        poly_dict = read_geojson(self.config['network']['polygon'][0])  # It can only read in one geojson
        poly = geojson_to_shp(poly_dict)

        if self.config['network']['road_types'] == 'none':
            # The user specified only the network type.
            G_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.config['network']['network_type'],
                                                 simplify=False, retain_all=True)
        elif self.config['network']['network_type'] == 'none':
            # The user specified only the road types.
            cf = ('["highway"~"{}"]'.format(self.config['network']['road_types'].replace(',', '|')))
            G_complex = osmnx.graph_from_polygon(polygon=poly, custom_filter=cf, simplify=False, retain_all=True)
        else:
            # The user specified the network type and road types.
            cf = ('["highway"~"{}"]'.format(self.config['network']['road_types'].replace(',', '|')))
            G_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.config['network']['network_type'],
                                                 custom_filter=cf, simplify=False, retain_all=True)

        logging.info('Graph downloaded from OSM with {:,} nodes and {:,} edges'.format(len(list(G_complex.nodes())),
                                                                                       len(list(G_complex.edges()))))

        # Depending on the types of analyses the user want to execute, it creates different kinds of graphs.
        G_simple, edges_complex = None, None
        if 'direct' in self.config:
            # Create 'edges_complex', convert complex graph to geodataframe
            logging.info('Start converting the graph to a geodataframe')
            edges_complex, _ = graph_to_gdf(G_complex)
            # edges_simple, nodes_simple = graph_to_gdf(G_simple)
            logging.info('Finished converting the graph to a geodataframe')

        if 'indirect' in self.config:
            # Create 'G_simple'
            G_simple = simplify_graph_count(G_complex)
            G_simple = graph_create_unique_ids(G_simple, 'unique_fid')

            # If the user wants to use undirected graphs, turn into an undirected graph (default).
            if self.config['network']['directed'] == 'false':
                if type(G_simple) == nx.classes.multidigraph.MultiDiGraph:
                    G_simple = G_simple.to_undirected()

        return G_simple, edges_complex

    def add_od_nodes(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        return

    def save_network(self, to_save, name, types=['pickle']):
        """Saves a geodataframe or graph to output_path"""
        if type(to_save) == gpd.GeoDataFrame:
            # The file that needs to be saved is a geodataframe
            if 'pickle' in types:
                with open(str(self.config['static'] / 'output_graph' / (name + '_base_network.p')), 'wb') as handle:
                    pickle.dump(to_save, handle)

                logging.info(f"Saved {name + '_base_network.p'} as pickle in {self.config['static'] / 'output_graph'}.")
        elif type(to_save) == nx.classes.multidigraph.MultiDiGraph:
            # The file that needs to be saved is a graph
            if 'shp' in types:
                graph_to_shp(to_save, self.config['static'] / 'output_graph' / (name + '_edges.shp'),
                             self.config['static'] / 'output_graph' / (name + '_nodes.shp'))
                logging.info(f"Saved {name + '_edges.shp'} and {name + '_nodes.shp'} as shapefiles in {self.config['static'] / 'output_graph'}.")
            if 'pickle' in types:
                nx.write_gpickle(to_save, self.config['static'] / 'output_graph' / (name + '_base_graph.gpickle'), protocol=4)
                logging.info(f"Saved {name + '_base_graph.gpickle'} as gpickle in {self.config['static'] / 'output_graph'}.")

        return

    def create(self):
        """Function with the logic to call the right analyses."""

        # Create the network from the network source
        if self.config['network']['source'] == 'shapefile':
            logging.info('Start creating a network from the submitted shapefile.')
            G, edge_gdf = self.network_shp()
        elif self.config['network']['source'] == 'OSM PBF':
            logging.info('Start creating a network from an OSM PBF file.')
            roadTypes = self.config['network']['road_types'].lower().replace(' ', ' ').split(',')
            G, edge_gdf = self.network_osm_pbf()  # in case of save shapes add here path
        elif self.config['network']['source'] == 'OSM download':
            logging.info('Start downloading a network from OSM.')
            G, edge_gdf = self.network_osm_download()
        elif self.config['network']['source'] == 'pickle':
            logging.info('G_simple already exists, uses the existing one!: {}'.format(G_simple_path))
            logging.info('edge_complex already exists, uses the existing one!: {}'.format(edges_complex_path))
            # CONVERT GRAPHS TO GEODATAFRAMES
            G = nx.read_gpickle(G_simple_path)
            with open(edges_complex_path, 'rb') as f:
                edge_gdf = pickle.load(f)

        # Save the 'base' network as gpickle.
        if G:
            # Check if all geometries between nodes are there, if not, add them as a straight line.
            G = add_missing_geoms_graph(G, geom_name='geometry')
            self.save_network(G, self.config['network']['name'], types=['pickle'])
        if edge_gdf:
            self.save_network(edge_gdf, self.config['network']['name'], types=['pickle'])

        return G, edge_gdf


class Hazard:
    def __init__(self, graph):
        self.something = 'bla'
        self.g = graph

    def overlay_hazard_raster(self):
        """Overlays the hazard raster over the road segments."""

        return

    def overlay_hazard_shp(self):
        """Overlays the hazard shapefile over the road segments."""
        return

    def join_hazard_table(self):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        return

    def hazard_intersect(self):
        self.g = add_missing_geoms_graph(self.g, geom_name='geometry')  # CHECK THE FUNCTION


def graph_create_unique_ids(graph, new_id_name):
    # Check if new_id_name exists and if unique
    u, v, k = list(graph.edges)[0]
    if new_id_name not in graph.edges[u, v, k]:
        # TODO: decide if we always add a new ID (in iGraph this is different)
        # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
        for i, (u, v, k) in enumerate(graph.edges(keys=True)):
            graph[u][v][k][new_id_name] = i + 1
        print("Added a new unique identifier field '{}'.".format(new_id_name))
        return graph
    else:
        return graph


def add_missing_geoms_graph(graph, geom_name='geometry'):
    # Not all nodes have geometry attributed (some only x and y coordinates) so add a geometry columns
    nodes_without_geom = [n[0] for n in graph.nodes(data=True) if geom_name not in n[-1]]
    for nd in nodes_without_geom:
        graph.nodes[nd][geom_name] = Point(graph.nodes[nd]['x'], graph.nodes[nd]['y'])

    edges_without_geom = [e for e in graph.edges.data(keys=True) if geom_name not in e[-1]]
    for ed in edges_without_geom:
        graph[ed[0]][ed[1]][ed[2]][geom_name] = LineString(
            [graph.nodes[ed[0]][geom_name], graph.nodes[ed[1]][geom_name]])

    return graph


def graph_to_gdf(G, save_nodes=False, save_edges=True, to_save=False):
    """Takes in a networkx graph object and returns edges and nodes as geodataframes
    Arguments:
        G (Graph): networkx graph object to be converted

    Returns:
        edges (GeoDataFrame) : containes the edges
        nodes (GeoDataFrame) :
    """

    nodes, edges = None, None

    if save_nodes and save_edges:
        nodes, edges = osmnx.graph_to_gdfs(G, nodes=save_nodes, edges=save_edges)

        if to_save:
            dfs = [edges, nodes]
            for df in dfs:
                for col in df.columns:
                    if df[col].dtype == np_object and col != df.geometry.name:
                        df[col] = df[col].astype(str)

    elif not save_nodes and save_edges:
        edges = osmnx.graph_to_gdfs(G, nodes=save_nodes, edges=save_edges)
    elif save_nodes and not save_edges:
        nodes = osmnx.graph_to_gdfs(G, nodes=save_nodes, edges=save_edges)

    return edges, nodes


def simplify_graph_count(G_complex):
    # Simplify the graph topology and log the change in nr of nodes and edges.
    old_len_nodes = G_complex.number_of_nodes()
    old_len_edges = G_complex.number_of_edges()

    G_simple = simplify_graph(G_complex)

    new_len_nodes = G_simple.number_of_nodes()
    new_len_edges = G_simple.number_of_edges()

    logging.info(
        'Graph simplified from {:,} to {:,} nodes and {:,} to {:,} edges.'.format(old_len_nodes, new_len_nodes, old_len_edges, new_len_edges))

    return G_simple


def graph_to_shp(G, edge_shp, node_shp):
    """Takes in a networkx graph object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:

        G []: networkx graph object to be converted

        edge_shp [str]: output path including extension for edges shapefile

        node_shp [str]: output path including extension for nodes shapefile

    Returns:

        None

    """

    # The nodes should have a geometry attribute (perhaps on top of the x and y attributes)
    nodes, edges = osmnx.graph_to_gdfs(G, node_geometry=False)

    dfs = [edges, nodes]
    for df in dfs:
        for col in df.columns:
            if df[col].dtype == np_object and col != df.geometry.name:
                df[col] = df[col].astype(str)

    print('\nSaving nodes as shapefile: {}'.format(node_shp))
    print('\nSaving edges as shapefile: {}'.format(edge_shp))

    nodes.to_file(node_shp, driver='ESRI Shapefile', encoding='utf-8')
    edges.to_file(edge_shp, driver='ESRI Shapefile', encoding='utf-8')


def read_geojson(geojson_file):
    """Read a GeoJSON file into a GeoJSON object.
    From the script get_rcm.py from Martijn Kwant.
    """
    with open(geojson_file) as f:
        return geojson.load(f)


def geojson_to_shp(geojson_obj, feature_number=0):
    """Convert a GeoJSON object to a Shapely Polygon.
    Adjusted from the script get_rcm.py from Martijn Kwant.

    In case of FeatureCollection, only one of the features is used (the first by default).
    3D points are converted to 2D.

    Parameters
    ----------
    geojson_obj : dict
        a GeoJSON object
    feature_number : int, optional
        Feature to extract polygon from (in case of MultiPolygon
        FeatureCollection), defaults to first Feature

    Returns
    -------
    polygon coordinates
        string of comma separated coordinate tuples (lon, lat) to be used by SentinelAPI
    """
    if 'coordinates' in geojson_obj:
        geometry = geojson_obj
    elif 'geometry' in geojson_obj:
        geometry = geojson_obj['geometry']
    else:
        geometry = geojson_obj['features'][feature_number]['geometry']

    def ensure_2d(geometry):
        if isinstance(geometry[0], (list, tuple)):
            return list(map(ensure_2d, geometry))
        else:
            return geometry[:2]

    def check_bounds(geometry):
        if isinstance(geometry[0], (list, tuple)):
            return list(map(check_bounds, geometry))
        else:
            if geometry[0] > 180 or geometry[0] < -180:
                raise ValueError('Longitude is out of bounds, check your JSON format or data. The Coordinate Reference System should be in EPSG:4326.')
            if geometry[1] > 90 or geometry[1] < -90:
                raise ValueError('Latitude is out of bounds, check your JSON format or data. The Coordinate Reference System should be in EPSG:4326.')

    # Discard z-coordinate, if it exists
    geometry['coordinates'] = ensure_2d(geometry['coordinates'])
    check_bounds(geometry['coordinates'])

    # Create a shapely polygon from the coordinates.
    poly = shape(geometry).buffer(0)
    return poly
