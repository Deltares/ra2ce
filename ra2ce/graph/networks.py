# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

# external modules
import logging
import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
import osmnx
import geojson
import pickle
import os
from pathlib import Path
from osmnx.simplification import simplify_graph
from numpy import object as np_object
from statistics import mean
from shapely.geometry import shape, Point, LineString
from .networks_utils import *


class Network:
    def __init__(self, config):
        self.config = config
        self.save_shp = True if config['network']['save_shp'] == 'true' else False
        self.network_name = self.config['network']['name'].replace(' ', '_')
        self.primary_files = config['network']['primary_file']
        self.diversion_files = config['network']['diversion_file']
        self.file_id = config['network']['file_id']
        self.snapping = config['network']['snapping_threshold']
        self.pruning = config['network']['pruning_threshold']
        self.name = config['project']['name']
        self.output_path = config['static'] / "output_graph"


    def network_shp(self, crs=4326):
        """Creates a (graph) network from a shapefile
        Args:
            name (string): name of the analysis given by user (will be part of the name of the output files)
            InputDict (dict): dictionairy with paths/input that is used to create the network
            crs (int): the EPSG number of the coordinate reference system that is used
            snapping (bool): True if snapping is required, False if not
            SnappingThreshold (int/float): threshold to reach another vertice to connect the edge to
            pruning (bool): True if pruning is required, False if not
            PruningThreshold (int/float): edges smaller than this length (threshold) are removed
        Returns:
            G (networkX graph): The resulting network graph
        """

        lines = self.read_merge_shp()
        logging.info("Function [read_merge_shp]: executed with {} {}".format(self.primary_files, self.diversion_files))
        aadt_names = None

        # Multilinestring to linestring
        # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
        # The list of fid's is reduced by the fid's that are not anymore in the merged lines
        edges, lines_merged = merge_lines_shpfiles(lines, self.file_id, aadt_names, crs)
        logging.info("Function [merge_lines_shpfiles]: executed with properties {}".format(list(edges.columns)))

        edges, id_name = gdf_check_create_unique_ids(edges, self.file_id)

        if self.snapping is not None or self.pruning is not None:
            if self.snapping is not None:
                edges = snap_endpoints_lines(edges, self.snapping, id_name, tolerance=1e-7)
                logging.info("Function [snap_endpoints_lines]: executed with threshold = {}".format(self.snapping))

        # merge merged lines if there are any merged lines
        if not lines_merged.empty:
            # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
            lines_merged.to_file(os.path.join(self.output_path, "{}_lines_that_merged.shp".format(self.name)))
            logging.info("Function [edges_to_shp]: saved at ".format(os.path.join(self.output_path, '{}_lines_that_merged'.format(self.name))))


        # Get the unique points at the end of lines and at intersections to create nodes
        nodes = create_nodes(edges, crs)
        logging.info("Function [create_nodes]: executed")

        if self.snapping is not None or self.pruning is not None:
            if self.snapping is not None:
                # merged lines may be updated when new nodes are created which makes a line cut in two
                edges = cut_lines(edges, nodes, id_name, tolerance=1e-4)
                nodes = create_nodes(edges, crs)
                logging.info("Function [cut_lines]: executed")

        # create tuples from the adjecent nodes and add as column in geodataframe
        resulting_network = join_nodes_edges(nodes, edges, id_name)
        resulting_network.crs = {'init': 'epsg:{}'.format(crs)}  # set the right CRS

        # Save geodataframe of the resulting network to
        resulting_network.to_pickle(
            os.path.join(self.output_path, '{}_gdf.pkl'.format(self.name)))
        logging.info("Saved network to pickle in ".format(os.path.join(self.output_path, '{}_gdf.pkl'.format(self.name))))



        # Create networkx graph from geodataframe
        G = graph_from_gdf(resulting_network, nodes)
        logging.info("Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(self.name))

        # Save graph to gpickle to use later for analysis
        nx.write_gpickle(G, os.path.join(self.output_path, '{}_graph.gpickle'.format(self.name)), protocol=4)
        logging.info("Saved graph to pickle in {}".format(os.path.join(self.output_path, '{}_graph.gpickle'.format(self.name))))

        # Save graph to shapefile for visual inspection
        graph_to_shp(G, os.path.join(self.output_path, '{}_edges.shp'.format(self.name)),
                     os.path.join(self.output_path, '{}_nodes.shp'.format(self.name)))

        return G, resulting_network

    def read_merge_shp(self, crs_=4326):
        """Imports shapefile(s) and saves attributes in a pandas dataframe.

        Args:
            shapefileAnalyse (string or list of strings): absolute path(s) to the shapefile(s) that will be used for analysis
            shapefileDiversion (string or list of strings): absolute path(s) to the shapefile(s) that will be used to calculate alternative routes but is not analysed
            idName (string): the name of the Unique ID column
            crs_ (int): the EPSG number of the coordinate reference system that is used
        Returns:
            lines (list of shapely LineStrings): full list of linestrings
            properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
        """

        # read shapefiles and add to list with path
        if isinstance(self.primary_files, str):
            shapefiles_analysis = [self.config['static'] / "network" / shp for shp in self.primary_files.split(',')]
        if isinstance(self.diversion_files, str):
            shapefiles_diversion = [self.config['static'] / "network" / shp for shp in self.diversion_files.split(',')]

        def read_file(file, analyse=1):
            """"Set analysis to 1 for main analysis and 0 for diversion network"""
            shp = gpd.read_file(file)
            shp['to_analyse'] = analyse
            return shp

        # concatenate all shapefile into one geodataframe and set analysis to 1 or 0 for diversions
        lines = [read_file(shp) for shp in shapefiles_analysis]
        if isinstance(self.diversion_files, str):
            [lines.append(read_file(shp, 0)) for shp in shapefiles_diversion]
        lines = pd.concat(lines)

        lines.crs = {'init': 'epsg:{}'.format(crs_)}

        # append the length of the road stretches
        lines['length'] = lines['geometry'].apply(lambda x: line_length(x))

        if lines['geometry'].apply(lambda row: isinstance(row, MultiLineString)).any():
            for line in lines.loc[lines['geometry'].apply(lambda row: isinstance(row, MultiLineString))].iterrows():
                if len(linemerge(line[1].geometry)) > 1:
                    warnings.warn("Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(
                            self.file_id, line[1][self.file_id]))

        print('Shapefile(s) loaded with attributes: {}.'.format(list(lines.columns.values)))  # fill in parameter names

        return lines

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
            graph_simple (Graph) : Simplified graph (for use in the indirect analyses)
            graph_complex_edges (GeoDataFrame : Complex graph (for use in the direct analyses)
        """
        poly_dict = read_geojson(self.config['network']['polygon'][0])  # It can only read in one geojson
        poly = geojson_to_shp(poly_dict)

        if self.config['network']['road_types'] == 'none':
            # The user specified only the network type.
            graph_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.config['network']['network_type'],
                                                 simplify=False, retain_all=True)
        elif self.config['network']['network_type'] == 'none':
            # The user specified only the road types.
            cf = ('["highway"~"{}"]'.format(self.config['network']['road_types'].replace(',', '|')))
            graph_complex = osmnx.graph_from_polygon(polygon=poly, custom_filter=cf, simplify=False, retain_all=True)
        else:
            # The user specified the network type and road types.
            cf = ('["highway"~"{}"]'.format(self.config['network']['road_types'].replace(',', '|')))
            graph_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.config['network']['network_type'],
                                                 custom_filter=cf, simplify=False, retain_all=True)

        logging.info('graph downloaded from OSM with {:,} nodes and {:,} edges'.format(len(list(graph_complex.nodes())),
                                                                                       len(list(graph_complex.edges()))))

        # Depending on the types of analyses the user want to execute, it creates different kinds of graphs.
        graph_simple, edges_complex = None, None
        if 'direct' in self.config:
            # Create 'edges_complex', convert complex graph to geodataframe
            logging.info('Start converting the graph to a geodataframe')
            edges_complex, _ = graph_to_gdf(graph_complex)
            # edges_simple, nodes_simple = graph_to_gdf(graph_simple)
            logging.info('Finished converting the graph to a geodataframe')

        if 'indirect' in self.config:
            # Create 'graph_simple'
            graph_simple = simplify_graph_count(graph_complex)
            graph_simple = graph_create_unique_ids(graph_simple, 'unique_fid')

            # If the user wants to use undirected graphs, turn into an undirected graph (default).
            if self.config['network']['directed'] == 'false':
                if type(graph_simple) == nx.classes.multidigraph.MultiDiGraph:
                    graph_simple = graph_simple.to_undirected()

        return graph_simple, edges_complex

    def add_od_nodes(self, G, od_analyses):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        from .origins_destinations import read_OD_files, create_OD_pairs, add_od_nodes

        graphs = {}
        for od_analysis in od_analyses:
            name = od_analysis['name'].replace(' ', '_')
            # Add the origin/destination nodes to the network
            ods = read_OD_files(od_analysis['origins'], od_analysis['origins_names'],
                                od_analysis['destinations'], od_analysis['destinations_names'],
                                od_analysis['id_name_origin_destination'], 'epsg:4326')  # TODO: decide if change CRS to flexible instead of just epsg:4326

            ods = create_OD_pairs(ods, G, id_name='unique_fid')

            # Save the OD pairs (GeoDataFrame) as pickle
            with open(str(self.config['output'] / od_analysis['analysis'] / (name + '_origins_destinations.p')), 'wb') as handle:
                pickle.dump(ods, handle)
            logging.info(f"Saved {name + '_origins_destinations.p'} in {self.config['output'] / od_analysis['analysis']}.")

            # Save the OD pairs (GeoDataFrame) as shapefile
            if od_analysis['save_shp'] == 'true':
                ods.to_file(self.config['static'] / od_analysis['analysis'] / (name + '_origins_destinations.shp'))
                logging.info(f"Saved {name + '_origins_destinations.shp'} in {self.config['output'] / od_analysis['analysis']}.")

            G = add_od_nodes(G, ods, id_name='unique_fid')
            graphs[od_analysis['name'].replace(' ', '_')] = G

        return graphs

    def save_network(self, to_save, name, types=['pickle']):
        """Saves a geodataframe or graph to output_path"""
        if type(to_save) == gpd.GeoDataFrame:
            # The file that needs to be saved is a geodataframe
            if 'pickle' in types:
                with open(str(self.config['static'] / 'output_graph' / (name + '_base_network.p')), 'wb') as handle:
                    pickle.dump(to_save, handle)

                logging.info(f"Saved {name + '_base_network.p'} in {self.config['static'] / 'output_graph'}.")
            if 'shp' in types:
                to_save.to_file(self.config['static'] / 'output_graph' / (name + '_base_network.shp'))
                logging.info(f"Saved {name + '_base_network.shp'} in {self.config['static'] / 'output_graph'}.")
        elif type(to_save) == nx.classes.multigraph.MultiGraph:
            # The file that needs to be saved is a graph
            if 'shp' in types:
                graph_to_shp(to_save, self.config['static'] / 'output_graph' / (name + '_edges.shp'),
                             self.config['static'] / 'output_graph' / (name + '_nodes.shp'))
                logging.info(f"Saved {name + '_edges.shp'} and {name + '_nodes.shp'} in {self.config['static'] / 'output_graph'}.")
            if 'pickle' in types:
                nx.write_gpickle(to_save, self.config['static'] / 'output_graph' / (name + '_base_graph.gpickle'), protocol=4)
                logging.info(f"Saved {name + '_base_graph.gpickle'} in {self.config['static'] / 'output_graph'}.")

    def create(self):
        """Function with the logic to call the right analyses."""
        # Initialize the variables for the graph and network.
        G, edge_gdf = None, None

        # Create the network from the network source
        if self.config['network']['source'] == 'shapefile':
            logging.info('Start creating a network from the submitted shapefile.')
            G, edge_gdf = self.network_shp()
        elif self.config['network']['source'] == 'OSM PBF':
            logging.info('Start creating a network from an OSM PBF file.')
            roadTypes = self.config['network']['road_types'].lower().replace(' ', ' ').split(',')
            G, edge_gdf = self.network_osm_pbf()
        elif self.config['network']['source'] == 'OSM download':
            logging.info('Start downloading a network from OSM.')
            G, edge_gdf = self.network_osm_download()
        elif self.config['network']['source'] == 'pickle':
            edges_complex_path = self.config['static'] / 'output_graph' / (self.network_name + '_base_network.p')
            G_simple_path = self.config['static'] / 'output_graph' / (self.network_name + '_base_graph.gpickle')

            if 'direct' in self.config:
                try:
                    with open(edges_complex_path, 'rb') as f:
                        edge_gdf = pickle.load(f)
                        logging.info(f"Using an existing network: {self.network_name + '_base_network.p'}")
                except FileNotFoundError as e:
                    logging.error(f"The network cannot be found in {edges_complex_path}.", e)
                    exit()
            if 'indirect' in self.config:
                try:
                    G = nx.read_gpickle(G_simple_path)
                    logging.info(f"Using an existing graph: {self.network_name + '_base_graph.gpickle'}")
                except FileNotFoundError as e:
                    logging.error(f"The graph cannot be found in {G_simple_path}.", e)
                    exit()

        # Create a dictionary of graphs per (indirect) analysis
        graph_dict = {}

        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = ['pickle'] if not self.save_shp else ['pickle', 'shp']
        if G:
            # Check if all geometries between nodes are there, if not, add them as a straight line.
            G = add_missing_geoms_graph(G, geom_name='geometry')
            self.save_network(G, self.network_name, types=to_save)
            graph_dict['base'] = G
        if edge_gdf:
            self.save_network(edge_gdf, self.network_name, types=to_save)

        if 'indirect' in self.config:
            if any('multi_link_origin_destination' in a['analysis'] for a in self.config['indirect']):
                # Check which analyses require origin and destination nodes to be added to the graph and which ones already have been created.
                use_existing_od = [a for a in self.config['indirect'] if (a['analysis'] in ['optimal_route_origin_destination', 'multi_link_origin_destination']) and ('origins' not in a) and ('destinations' not in a)]
                if len(use_existing_od) > 0:
                    for existing in use_existing_od:
                        read_existing = self.config['static'] / 'output_graph' / (existing['name'].replace(' ', '_') + '_base_graph.gpickle')
                        try:
                            graph_dict[existing['name']] = nx.read_gpickle(read_existing)
                            logging.info(f"Existing graph found in {read_existing}.")
                        except FileNotFoundError as e:
                            logging.error(f"The graph cannot be found in {read_existing}.", e)
                            exit()

                create_new_od = [a for a in self.config['indirect'] if (a['analysis'] in ['optimal_route_origin_destination', 'multi_link_origin_destination']) and ('origins' in a) and ('destinations' in a)]
                if len(create_new_od) > 0:
                    # Origin and destination nodes should be added to the graph.
                    od_graphs = self.add_od_nodes(G, create_new_od)
                    for n in od_graphs.keys():
                        self.save_network(od_graphs[n], n, types=to_save)
                    graph_dict.update(od_graphs)
            if any('hazard_map' in a for a in self.config['indirect']):
                # There is a hazard map or multiple hazard maps that should be intersected with the graph.
                to_overlay_hazard = [(a['name'], a['analysis'], a['hazard_map'], a['aggregate_wl']) for a in self.config['indirect'] if ('hazard_map' in a)]

                for n, a, h, wl in to_overlay_hazard:
                    if a == 'multi_link_redundancy':
                        haz = Hazard(graph_dict['base'], h, wl)
                        graph_dict[n + '_hazard'] = haz.hazard_intersect()
                    if a == 'multi_link_origin_destination':
                        haz = Hazard(graph_dict[n], h, wl)
                        graph_dict[n + '_hazard'] = haz.hazard_intersect()

        if 'direct' in self.config:
            haz = Hazard(edge_gdf, h)
        return G, edge_gdf


class Hazard:
    def __init__(self, graph_gdf, list_hazard_files, aggregate_wl):
        self.list_hazard_files = list_hazard_files
        self.aggregate_wl = aggregate_wl
        if type(graph_gdf) == gpd.GeoDataFrame:
            self.gdf = graph_gdf
            self.g = None
        else:
            self.gdf = None
            self.g = graph_gdf

    def overlay_hazard_raster(self, hf):
        """Overlays the hazard raster over the road segments."""
        # GeoTIFF
        import rasterio
        src = rasterio.open(hf)

        # Name the attribute name the name of the hazard file
        hn = hf.stem

        # check which road is overlapping with the flood and append the flood depth to the graph
        for u, v, k, edata in self.g.edges.data(keys=True):
            if 'geometry' in edata:
                # check how long the road stretch is and make a point every other meter
                nr_points = round(edata['length'])
                if nr_points == 1:
                    coords_to_check = list(edata['geometry'].boundary)
                else:
                    coords_to_check = [edata['geometry'].interpolate(i / float(nr_points - 1), normalized=True) for
                                       i in range(nr_points)]
                crds = []
                for c in coords_to_check:
                    # check if part of the linestring is inside the flood extent
                    if (src.bounds.left < c.coords[0][0] < src.bounds.right) and (
                            src.bounds.bottom < c.coords[0][1] < src.bounds.top):
                        crds.append(c.coords[0])
                if crds:
                    # the road lays inside the flood extent
                    if self.aggregate_wl == 'max':
                        if (max([x.item(0) for x in src.sample(crds)]) > 999999) | (
                                max([x.item(0) for x in src.sample(crds)]) < -999999):
                            # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                            self.g[u][v][k][hn] = 0
                        else:
                            self.g[u][v][k][hn] = max([x.item(0) for x in src.sample(crds)])
                    elif self.aggregate_wl == 'min':
                        if (min([x.item(0) for x in src.sample(crds)]) > 999999) | (
                                min([x.item(0) for x in src.sample(crds)]) < -999999):
                            # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                            self.g[u][v][k][hn] = 0
                        else:
                            self.g[u][v][k][hn] = min([x.item(0) for x in src.sample(crds)])
                    elif self.aggregate_wl == 'mean':
                        if (mean([x.item(0) for x in src.sample(crds)]) > 999999) | (
                                mean([x.item(0) for x in src.sample(crds)]) < -999999):
                            # the road is most probably in the 'no data' area of the raster (usually a very large or small number is used as 'no data' value)
                            self.g[u][v][k][hn] = 0
                        else:
                            self.g[u][v][k][hn] = mean([x.item(0) for x in src.sample(crds)])
                    else:
                        logging.warning("No aggregation method is chosen ('max', 'min' or 'mean).")
                else:
                    self.g[u][v][k][hn] = 0
            else:
                self.g[u][v][k][hn] = 0

    def overlay_hazard_shp(self, hf):
        """Overlays the hazard shapefile over the road segments."""
        # Shapefile
        gdf = gpd.read_file(hf)
        spatial_index = gdf.sindex

        for u, v, k, edata in self.g.edges.data(keys=True):
            if 'geometry' in edata:
                possible_matches_index = list(spatial_index.intersection(edata['geometry'].bounds))
                possible_matches = gdf.iloc[possible_matches_index]
                precise_matches = possible_matches[possible_matches.intersects(edata['geometry'])]
                # TODO REQUEST USER TO INPUT THE COLUMN NAME OF THE HAZARD COLUMN
                hn='TODO'
                if not precise_matches.empty:
                    if self.aggregate_wl == 'max':
                        self.g[u][v][k][hn] = precise_matches[hn].max()
                    if self.aggregate_wl == 'min':
                        self.g[u][v][k][hn] = precise_matches[hn].min()
                    if self.aggregate_wl == 'mean':
                        self.g[u][v][k][hn] = precise_matches[hn].mean()
                else:
                    self.g[u][v][k][hn] = 0
            else:
                self.g[u][v][k][hn] = 0
        return

    def join_hazard_table(self):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs."""
        return

    def hazard_intersect(self):
        for hf in self.list_hazard_files:
            if hf.suffix == '.tif':
                self.overlay_hazard_raster(hf)
            elif hf.suffix == '.shp':
                self.overlay_hazard_shp(hf)
            elif hf.suffix in ['.csv', '.json']:
                self.join_hazard_table(hf)

        return self.g


def graph_create_unique_ids(graph, new_id_name):
    # Check if new_id_name exists and if unique
    u, v, k = list(graph.edges)[0]
    if new_id_name not in graph.edges[u, v, k]:
        # TODO: decide if we always add a new ID (in iGraph this is different)
        # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
        for i, (u, v, k) in enumerate(graph.edges(keys=True)):
            graph[u][v][k][new_id_name] = i + 1
        logging.info("Added a new unique identifier field '{}'.".format(new_id_name))
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


def read_merge_shp(shapefileAnalyse,  idName, shapefileDiversion=[], crs_=4326):
    """Imports shapefile(s) and saves attributes in a pandas dataframe.

    Args:
        shapefileAnalyse (string or list of strings): absolute path(s) to the shapefile(s) that will be used for analysis
        shapefileDiversion (string or list of strings): absolute path(s) to the shapefile(s) that will be used to calculate alternative routes but is not analysed
        idName (string): the name of the Unique ID column
        crs_ (int): the EPSG number of the coordinate reference system that is used
    Returns:
        lines (list of shapely LineStrings): full list of linestrings
        properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
    """

    # convert shapefile names to a list if it was not already a list
    if isinstance(shapefileAnalyse, str):
        shapefileAnalyse = [shapefileAnalyse]
    if isinstance(shapefileDiversion, str):
        shapefileDiversion = [shapefileDiversion]

    lines = []

    # read the shapefile(s) for analysis
    for shp in shapefileAnalyse:
        lines_shp = gpd.read_file(shp)
        lines_shp['to_analyse'] = 1
        lines.append(lines_shp)

    # read the shapefile(s) for only diversion
    if isinstance(shapefileDiversion, list):
        for shp2 in shapefileDiversion:
            lines_shp = gpd.read_file(shp2)
            lines_shp['to_analyse'] = 0
            lines.append(lines_shp)

    # concatenate all shapefiles into one geodataframe
    lines = pd.concat(lines)
    lines.crs = {'init': 'epsg:{}'.format(crs_)}

    # append the length of the road stretches
    lines['length'] = lines['geometry'].apply(lambda x: line_length(x))

    if lines['geometry'].apply(lambda row: isinstance(row, MultiLineString)).any():
        for line in lines.loc[lines['geometry'].apply(lambda row: isinstance(row, MultiLineString))].iterrows():
            if len(linemerge(line[1].geometry)) > 1:
                warnings.warn(
                    "Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(
                        idName, line[1][idName]))

    print('Shapefile(s) loaded with attributes: {}.'.format(list(lines.columns.values)))  # fill in parameter names

    return lines

