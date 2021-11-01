# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
@author: M. Kwant, Deltares
"""
import sys
sys.path.append(r"d:\ra2ceMaster\trails-master\src\trails")

# external modules
from osgeo import gdal
import numpy as np
import time
from pyrosm import OSM, get_data
import igraph as ig

# local modules
from .networks_utils import *


# edge_attributes = dict(area="sum", bridge="concat", foot="ignore", 'highway'="concat",
#                  'junction',
#                  'lanes',
#                  'name',
#                  'oneway',
#                  'ref',
#                  'service',
#                  'surface',
#                  'tracktype',
#                  'tunnel',
#                  'width',
#                  'id',
#                  'timestamp',
#                  'version',
#                  'tags',
#                  'osm_type',
#                  'geometry',
#                  'u',
#                  'v',
#                  'length',
#                  'u_seq',
#                  'v_seq']


class Network:
    def __init__(self, config):
        # General
        self.config = config
        self.name = config['project']['name']
        self.output_path = config['static'] / "output_graph"

        # Network
        self.directed = config['network']['directed']
        self.source = config['network']['source']
        self.primary_files = config['network']['primary_file']
        self.diversion_files = config['network']['diversion_file']
        self.file_id = config['network']['file_id']
        self.polygon_file = config['network']['polygon']
        self.network_type = config['network']['network_type']
        self.road_types = config['network']['road_types']
        self.save_shp = config['network']['save_shp']

        # Origins and destinations
        self.origins = config['origins_destinations']['origins']
        self.destinations = config['origins_destinations']['destinations']
        self.origins_names = config['origins_destinations']['origins_names']
        self.destinations_names = config['origins_destinations']['destinations_names']
        self.id_name_origin_destination = config['origins_destinations']['id_name_origin_destination']

        # Hazard
        self.hazard_map = config['hazard']['hazard_map']
        self.aggregate_wl = config['hazard']['aggregate_wl']

        # Cleanup
        self.snapping = config['cleanup']['snapping_threshold']
        self.pruning = config['cleanup']['pruning_threshold']
        self.segmentation_length = config['cleanup']['segmentation_length']

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
        edges_complex = join_nodes_edges(nodes, edges, id_name)
        edges_complex.crs = {'init': 'epsg:{}'.format(crs)}  # set the right CRS

        # Save geodataframe of the resulting network to
        edges_complex.to_pickle(
            os.path.join(self.output_path, '{}_gdf.pkl'.format(self.name)))
        logging.info("Saved network to pickle in ".format(os.path.join(self.output_path, '{}_gdf.pkl'.format(self.name))))

        # Create networkx graph from geodataframe
        graph_complex = graph_from_gdf(edges_complex, nodes)
        logging.info("Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(self.name))

        # exporting complex graph because simple graph is not needed
        return graph_complex, edges_complex

    def network_osm_pbf(self):
        """Creates a network from an OSM PBF file.

        Arguments:
            *path_to_pbf* (Path) : Path to the osm_dump from which the road network is to be fetched
            *road_types* (list of strings) : The road types to fetch from the dump e.g. ['motorway', 'motorway_link']
            *save_files* (Path): Path where the output should be saved. Default: None
            *segmentation* (float): define lenghts of the cut segments. Default: None
            *save_shapes* (Path): Folder path where shapefiles should be saved. Default: None

        Returns:
            G_simple (Graph) : Simplified graph (for use in the indirect analyses)
            G_complex_edges (GeoDataFrame : Complex graph (for use in the direct analyses)

        """
        road_types = self.road_types.lower().replace(' ', ' ').split(',')

        # Initialize reader
        osm = OSM(str(self.primary_files[0]))

        # Read nodes and edges of the 'driving' network
        nodes, edges = osm.get_network(nodes=True, network_type="driving")

        # Create a graph for igraph from nodes and edges
        G_complex = osm.to_graph(nodes, edges, graph_type='igraph', force_bidirectional=True)

        # Create a GeoDataFrame from the graph
        edges_complex = pd.DataFrame([list(G_complex.es[x]) for x in G_complex.es.attribute_names()]).T
        edges_complex.columns = G_complex.es.attribute_names()
        edges_complex.dropna(axis=1, how='all', inplace=True)
        edges_complex = gpd.GeoDataFrame(edges_complex, geometry='geometry', crs='epsg:4326')

        #TODO: maybe simplify graph with trails scripts!!
        ## G_simple = G_complex.simplify(combine_edges=dict(weight=sum))
        G_complex = graph_create_unique_ids(G_complex, new_id_name='ra2ce_fid')

        if self.segmentation_length is not None:
            graph = Segmentation(edges_complex, self.segmentation_length)
            graph.apply_segmentation()

        return G_complex, edges_complex  #TODO: CHANGE TO G_simple when it is simplified

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
        poly_dict = read_geojson(self.polygon_file[0])  # It can only read in one geojson
        poly = geojson_to_shp(poly_dict)

        if not self.road_types:
            # The user specified only the network type.
            graph_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.network_type,
                                                 simplify=False, retain_all=True)
        elif not self.network_type:
            # The user specified only the road types.
            cf = ('["highway"~"{}"]'.format(self.road_types.replace(',', '|')))
            graph_complex = osmnx.graph_from_polygon(polygon=poly, custom_filter=cf, simplify=False, retain_all=True)
        else:
            # The user specified the network type and road types.
            cf = ('["highway"~"{}"]'.format(self.road_types.replace(',', '|')))
            graph_complex = osmnx.graph_from_polygon(polygon=poly, network_type=self.network_type,
                                                 custom_filter=cf, simplify=False, retain_all=True)

        logging.info('graph downloaded from OSM with {:,} nodes and {:,} edges'.format(len(list(graph_complex.nodes())),
                                                                                       len(list(graph_complex.edges()))))

        # Create 'edges_complex', convert complex graph to geodataframe
        logging.info('Start converting the graph to a geodataframe')
        edges_complex, nodes = graph_to_gdf(graph_complex)

        # edges_simple, nodes_simple = graph_to_gdf(graph_simple)
        logging.info('Finished converting the graph to a geodataframe')

        # Create 'graph_simple'
        graph_simple, graph_complex = create_simplified_graph(graph_complex)

        return graph_simple, edges_complex

    def add_od_nodes(self, graph):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        from .origins_destinations import read_OD_files, create_OD_pairs, add_od_nodes

        name = 'origin_destination_table'

        ods_file_path = self.config['static'] / 'output_graph' / (name + '.feather')
        if ods_file_path.is_file():
            ods = gpd.read_feather(ods_file_path)
            logging.info(f"Existing Origin-Destination table found in {ods_file_path.parent}.")
        else:
            # Add the origin/destination nodes to the network
            ods = read_OD_files(self.origins, self.origins_names,
                                self.destinations, self.destinations_names,
                                self.id_name_origin_destination, 'epsg:4326')

            ods = create_OD_pairs(ods, graph)
            ods.crs = 'epsg:4326'  # TODO: decide if change CRS to flexible instead of just epsg:4326

            # Save the OD pairs (GeoDataFrame) as pickle
            ods.to_feather(ods_file_path, index=False)
            logging.info(f"Saved {ods_file_path.stem} in {ods_file_path.parent}.")

        # Save the OD pairs (GeoDataFrame) as shapefile
        if self.save_shp:
            ods_path = self.config['static'] / 'output_graph' / (name + '.shp')
            ods.to_file(ods_path, index=False)
            logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        graph = add_od_nodes(graph, ods)

        return graph

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

    def save_network(self, to_save, name, types=['pickle']):
        """Saves a geodataframe or graph to output_path"""
        if type(to_save) == gpd.GeoDataFrame:
            # The file that needs to be saved is a geodataframe
            if 'pickle' in types:
                output_path_pickle = self.config['static'] / 'output_graph' / (name + '_network.feather')
                to_save.to_feather(output_path_pickle, index=False)
                logging.info(f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}.")
            if 'shp' in types:
                output_path = self.config['static'] / 'output_graph' / (name + '_network.shp')
                to_save.to_file(output_path, index=False)
                logging.info(f"Saved {output_path.stem} in {output_path.resolve().parent}.")

        elif type(to_save) == ig.Graph:
            # The file that needs to be saved is a graph
            # if 'shp' in types:  #TODO: just save the network geodataframe that is created to shp
            #     graph_to_shp(to_save, self.config['static'] / 'output_graph' / (name + '_edges.shp'),
            #                  self.config['static'] / 'output_graph' / (name + '_nodes.shp'))
            #     logging.info(f"Saved {name + '_edges.shp'} and {name + '_nodes.shp'} in {self.config['static'] / 'output_graph'}.")
            if 'pickle' in types:
                output_path_pickle = self.config['static'] / 'output_graph' / (name + '_graph.pickle')
                to_save.write_pickle(output_path_pickle, version=4)
                logging.info(f"Saved {output_path_pickle.stem} in {output_path_pickle.resolve().parent}.")
        return output_path_pickle

    def create(self, config_analyses):
        """Function with the logic to call the right analyses."""
        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = ['pickle'] if not self.save_shp else ['pickle', 'shp']

        # For all graph and networks - check if it exists, otherwise, make the graph and/or network.
        base_graph_path = self.config['static'] / 'output_graph' / 'base_graph.pickle'
        base_network_path = self.config['static'] / 'output_graph' / 'base_network.feather'
        if (base_graph_path.is_file()) and (base_network_path.is_file()):
            config_analyses['base_graph'] = base_graph_path
            config_analyses['base_network'] = base_network_path
            logging.info(f"Existing graph found: {base_graph_path}.")
            logging.info(f"Existing network found: {base_network_path}.")
        else:
            # Create the network from the network source
            if self.source == 'shapefile':
                logging.info('Start creating a network from the submitted shapefile.')
                base_graph, edge_gdf = self.network_shp()

            elif self.source == 'OSM PBF':
                logging.info('Start creating a network from an OSM PBF file.')

                base_graph, edge_gdf = self.network_osm_pbf()

            elif self.source == 'OSM download':
                logging.info('Start downloading a network from OSM.')
                base_graph, edge_gdf = self.network_osm_download()

            # Check if all geometries between nodes are there, if not, add them as a straight line.
            base_graph = add_missing_geoms_graph(base_graph, geom_name='geometry')

            # Make the graph directed or undirected
            if not self.directed:
                # The graph should be undirected
                if base_graph.is_directed():
                    base_graph = base_graph.as_undirected(mode=False)
                    # Change mode to 'collapse' and decide what to do with the attributes
                    # https://igraph.org/python/doc/api/igraph._igraph.GraphBase.html#to_undirected
                    # https://igraph.org/python/doc/api/igraph._igraph.GraphBase.html#simplify
            else:
                # The graph should be directed
                if not base_graph.is_directed():
                    base_graph = base_graph.as_directed()

            # Save the graph and geodataframe
            config_analyses['base_graph'] = self.save_network(base_graph, 'base', types=to_save)
            config_analyses['base_network'] = self.save_network(edge_gdf, 'base', types=to_save)

        if (self.origins is not None) and (self.destinations is not None):
            od_graph_path = self.config['static'] / 'output_graph' / 'origins_destinations_graph.pickle'
            if od_graph_path.is_file():
                config_analyses['origins_destinations_graph'] = od_graph_path
                logging.info(f"Existing graph found: {od_graph_path}.")
            else:
                # Origin and destination nodes should be added to the graph.
                if (base_graph_path.is_file()) or base_graph:
                    if base_graph_path.is_file():
                        base_graph = ig.Graph()
                        base_graph = base_graph.Read_Pickle(base_graph_path)
                    od_graph = self.add_od_nodes(base_graph)
                    config_analyses['origins_destinations_graph'] = self.save_network(od_graph, 'origins_destinations', types=to_save)

        if self.hazard_map is not None:
            # There is a hazard map or multiple hazard maps that should be intersected with the graph.
            # Overlay the hazard on the geodataframe as well (todo: combine with graph overlay if both need to be done?)
            base_graph_hazard_path = self.config['static'] / 'output_graph' / 'base_hazard_graph.pickle'
            if base_graph_hazard_path.is_file():
                config_analyses['base_hazard_graph'] = base_graph_hazard_path
                logging.info(f"Existing graph found: {base_graph_hazard_path}.")
            else:
                if (base_graph_path.is_file()) or base_graph:
                    if base_graph_path.is_file():
                        base_graph = nx.read_gpickle(base_graph_path)
                    haz = Hazard(base_graph, self.hazard_map, self.aggregate_wl)
                    base_graph_hazard = haz.hazard_intersect()
                    config_analyses['base_hazard_graph'] = self.save_network(base_graph_hazard, 'base_hazard', types=to_save)
                else:
                    logging.warning("No base graph found to intersect the hazard with. Check your network.ini file.")

            od_graph_hazard_path = self.config['static'] / 'output_graph' / 'origins_destinations_hazard_graph.pickle'
            if od_graph_hazard_path.is_file():
                config_analyses['origins_destinations_hazard_graph'] = od_graph_hazard_path
                logging.info(f"Existing graph found: {od_graph_hazard_path}.")
            else:
                if (od_graph_path.is_file()) or od_graph:
                    if od_graph_path.is_file():
                        od_graph = nx.read_gpickle(od_graph_path)
                    haz = Hazard(od_graph, self.hazard_map, self.aggregate_wl)
                    od_graph_hazard = haz.hazard_intersect()
                    config_analyses['origins_destinations_hazard_graph'] = self.save_network(od_graph_hazard,
                                                                                             'origins_destinations_hazard',
                                                                                             types=to_save)
                else:
                    logging.warning("No base graph found to intersect the hazard with. Check your network.ini file.")

            # Add the names of the hazard files to the config_analyses
            config_analyses['hazard_names'] = [haz.stem for haz in self.hazard_map]

        return config_analyses


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
        """Overlays the hazard raster over the road segments.

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """
        # Name the attribute name the name of the hazard file
        hazard_names = [f.stem for f in hf]

        # Check if the extent and resolution of the different hazard maps are the same.
        same_extent = check_hazard_extent_resolution(hf)
        if same_extent:
            extent = get_extent(gdal.Open(str(hf[0])))
            logging.info("The flood maps have the same extent. Flood maps used: {}".format(", ".join(hazard_names)))

        for i, hn in enumerate(hazard_names):
            src = gdal.Open(str(hf[i]))
            if not same_extent:
                extent = get_extent(src)
            raster_band = src.GetRasterBand(1)

            try:
                raster = raster_band.ReadAsArray()
                size_array = raster.shape
                logging.info("Getting water depth or surface water elevation values from {}".format(hn))
            except MemoryError as e:
                logging.warning(
                    "The raster is too large to read as a whole and will be sampled point by point. MemoryError: {}".format(
                        e))
                size_array = None
                nodatavalue = raster_band.GetNoDataValue()

            # check which road is overlapping with the flood and append the flood depth to the graph or geodataframe
            if self.g:
                for edge in self.g.es:
                    edge_id = edge.index
                    edata = edge.attributes()

                    if 'geometry' in edata:
                        # check how long the road stretch is and make a point every other meter
                        nr_points = round(edata['length'])
                        if nr_points == 1:
                            coords_to_check = list(edata['geometry'].boundary)
                        else:
                            coords_to_check = [edata['geometry'].interpolate(i / float(nr_points - 1), normalized=True) for
                                               i in range(nr_points)]

                        x_objects = np.array([c.coords[0][0] for c in coords_to_check])
                        y_objects = np.array([c.coords[0][1] for c in coords_to_check])

                        if size_array:
                            # Fastest method but be aware of out of memory errors!
                            water_level = sample_raster_full(raster, x_objects, y_objects, size_array, extent)
                        else:
                            # Slower method but no issues with memory errors
                            water_level = sample_raster(raster_band, nodatavalue, x_objects, y_objects, extent['minX'], extent['pixelWidth'], extent['maxY'], extent['pixelHeight'])

                        if len(water_level) > 0:
                            if self.aggregate_wl == 'max':
                                self.g.es[edge_id][hn+'_'+self.aggregate_wl] = water_level.max()
                            elif self.aggregate_wl == 'min':
                                self.g.es[edge_id][hn+'_'+self.aggregate_wl] = water_level.min()
                            elif self.aggregate_wl == 'mean':
                                self.g.es[edge_id][hn+'_'+self.aggregate_wl] = mean(water_level)
                            else:
                                logging.warning("No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'.")
                        else:
                            self.g.es[edge_id][hn+'_'+self.aggregate_wl] = np.nan

                    else:
                        self.g.es[edge_id][hn+'_'+self.aggregate_wl] = np.nan

            if self.gdf:
                print("Raster hazard overlay with gdf should be adjusted to how it should work with Kees' model")
            #     # The extent and resolution of the different hazard maps are the same, so the same points in polygons
            #     # can be used for all hazard maps (saves time to not compute them again for each hazard map).
            #     if not same_extent:
            #         points_in_polygons = find_points_in_polygon(self.gdf.geometry.values, extent)
            #     else:
            #         if k == 0:
            #             points_in_polygons = find_points_in_polygon(self.gdf.geometry.values, extent)
            #
            #     if size_array:
            #         # Fastest method but be aware of out of memory errors!
            #         total_water_levels = list()
            #         for pnts in points_in_polygons:
            #             x_objects = np.transpose(pnts)[0]
            #             y_objects = np.transpose(pnts)[1]
            #             water_level = sample_raster_full(raster, x_objects, y_objects, size_array, extent)
            #             total_water_levels.append(list(np.where(water_level <= 0, np.nan, water_level)))
            #     else:
            #         # Slower method but no issues with memory errors
            #         total_water_levels = water_level_at_points(points_in_polygons, extent, raster_band, nodatavalue)
            #
            #     if len(water_level) > 0:
            #         if self.aggregate_wl == 'max':
            #             self.gdf.loc[:, hn] = total_water_levels.max()
            #         elif self.aggregate_wl == 'min':
            #             self.g[u][v][k][hn] = water_level.min()
            #         elif self.aggregate_wl == 'mean':
            #             self.g[u][v][k][hn] = mean(water_level)
            #         else:
            #             logging.warning("No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'.")
            #     else:
            #         self.g[u][v][k][hn] = np.nan

    def overlay_hazard_shp(self, hf):
        """Overlays the hazard shapefile over the road segments.

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """
        #TODO differentiate between graph and geodataframe input

        # Shapefile
        gdf = gpd.read_file(hf)
        spatial_index = gdf.sindex

        for edge in self.g.es:
            edge_id = edge.index
            edata = edge.attributes()

            if 'geometry' in edata:
                possible_matches_index = list(spatial_index.intersection(edata['geometry'].bounds))
                possible_matches = gdf.iloc[possible_matches_index]
                precise_matches = possible_matches[possible_matches.intersects(edata['geometry'])]
                # TODO REQUEST USER TO INPUT THE COLUMN NAME OF THE HAZARD COLUMN
                hn='TODO'
                if not precise_matches.empty:
                    if self.aggregate_wl == 'max':
                        self.g.es[edge_id][hn+'_max'] = precise_matches[hn].max()
                    if self.aggregate_wl == 'min':
                        self.g.es[edge_id][hn+'_min'] = precise_matches[hn].min()
                    if self.aggregate_wl == 'mean':
                        self.g.es[edge_id][hn+'_mean'] = precise_matches[hn].mean()
                else:
                    self.g.es[edge_id][hn] = 0
            else:
                self.g.es[edge_id][hn] = 0
        return

    def join_hazard_table(self):
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs.

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        """
        # TODO differentiate between graph and geodataframe input
        return

    def hazard_intersect(self):
        hazards_tif = [haz for haz in self.list_hazard_files if haz.suffix == '.tif']
        hazards_shp = [haz for haz in self.list_hazard_files if haz.suffix == '.shp']
        hazards_table = [haz for haz in self.list_hazard_files if haz.suffix in ['.csv', '.json']]

        if len(hazards_tif) > 0:
            start = time.time()
            self.overlay_hazard_raster(hazards_tif)
            end = time.time()
            logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        elif len(hazards_shp) > 0:
            self.overlay_hazard_shp(hazards_shp)
        elif len(hazards_table) > 0:
            self.join_hazard_table(hazards_table)

        return self.g
