# -*- coding: utf-8 -*-
"""
Created on 31-8-2022
"""
# external modules
import pyproj
import time
from rasterstats import zonal_stats, point_query
from typing import Any, Union

# local modules
from .networks_utils import *
from ..io import *


class Hazard:
    """Class where the hazard overlay happens.

    Attributes:
        network: GeoDataFrame of the network.
        graphs: NetworkX graphs.
    """

    def __init__(self, network, graphs, files):
        self.config = network.config

        # graphs
        self.graphs = graphs

        # files
        self.files = files
        self.aggregate_wl = self.config['hazard']['aggregate_wl']
        self.hazard_files = {}  # Initiate the variable hazard_files
        self.get_hazard_files()

        # bookkeeping for the hazard map names
        self.hazard_name_table = self.get_hazard_name_table()
        self.hazard_names = list(dict.fromkeys(list(self.hazard_name_table['File name'])))
        self.ra2ce_names = list(dict.fromkeys([n[:-3] for n in self.hazard_name_table['RA2CE name']]))

    def overlay_hazard_raster_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the hazard raster over the road segments GeoDataFrame.

        Args:
            *graph* (GeoDataFrame) : GeoDataFrame that will be intersected with the hazard map raster.

        Returns:

        """
        assert type(gdf) == gpd.GeoDataFrame, "Network is not a GeoDataFrame"

        from tqdm import tqdm  # Doesn't work when imported at the top of the script

        ## beneden naar 1 methode
        # Validate input
        # Check if the extent and resolution of the different hazard maps are the same.
        same_extent = check_hazard_extent_resolution(self.hazard_files['tif'])  # property van Hazard
        if same_extent:
            extent = get_extent(gdal.Open(str(self.hazard_files['tif'][0])))
            logging.info(
                "The flood maps have the same extent. Flood maps used: {}".format(", ".join(self.hazard_names)))
        else:
            pass
            # Todo: what if they do not have the same extent?
        ## boven naar 1 methode

        ## Dit is 1 methode
        # Validate input
        # Check if network and raster overlap
        extent_graph = gdf.total_bounds
        extent_graph = (extent_graph[0], extent_graph[2], extent_graph[1], extent_graph[3])
        extent_hazard = (extent['minX'], extent['maxX'], extent['minY'], extent['maxY'])

        if not bounds_intersect_2d(extent_graph, extent_hazard):
            logging.info("Raster extent: {}, Graph extent: {}".format(extent, extent_graph))
            raise ValueError(
                "The hazard raster and the network geometries do not overlap, check projection")
        ## Tot hier

        # Make sure none of the geometries is a nonetype object (this will raise an error in zonal_stats)
        empty_entries = gdf.loc[gdf.geometry.isnull()]
        if not len(empty_entries) == 0:
            logging.warning(("Some geometries have NoneType objects (no coordinate information), namely: {}.".format(
                empty_entries) +
                             "This could  due  to segmentation, and might cause an exception in hazard  overlay"))

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            tqdm.pandas(desc="Network hazard overlay with " + hn)
            flood_stats = gdf.geometry.progress_apply(lambda x: zonal_stats(x, str(self.hazard_files['tif'][i]),
                                                                            all_touched=True,
                                                                            stats="min max mean"))
            gdf[rn + '_mi'] = [x[0]['min'] for x in flood_stats]
            gdf[rn + '_ma'] = [x[0]['max'] for x in flood_stats]
            gdf[rn + '_me'] = [x[0]['mean'] for x in flood_stats]

            tqdm.pandas(desc="Network fraction with hazard overlay with " + hn)
            gdf[rn + '_fr'] = gdf.geometry.progress_apply(
                lambda x: fraction_flooded(x, str(self.hazard_files['tif'][i])))
        return gdf

    def overlay_hazard_raster_graph(self, graph: nx.Graph) -> nx.Graph: #TODO: test if it is this type
        """Overlays the hazard raster over the road segments graph.

        Args:
            *hf* (list of Pathlib paths) : #not sure if this is needed as argument if we also read if from the config
            *graph* (NetworkX Graph) : NetworkX graph with geometries that will be intersected with the hazard map raster.

        Returns:
            *graph* (NetworkX Graph) : NetworkX graph with hazard values
        """
        from tqdm import tqdm

        # Verify the graph type (networkx)
        assert type(graph).__module__.split('.')[0] == 'networkx'
        extent_graph = get_graph_edges_extent(graph)

        # Get all edge geometries
        edges_geoms = [(u, v, k, edata) for u, v, k, edata in graph.edges.data(keys=True) if 'geometry' in edata]

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            extent = get_extent(gdal.Open(str(self.hazard_files['tif'][i])))
            extent_hazard = (extent['minX'], extent['maxX'], extent['minY'], extent['maxY'])

            if bounds_intersect_2d(extent_graph, extent_hazard):
                pass

            else:
                logging.info("Raster extent: {}, Graph extent: {}".format(extent, extent_graph))
                raise ValueError(
                    "The hazard raster and the graph geometries do not overlap, check projection")

            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(graph,
                                   {(u, v, k): {rn + '_' + self.aggregate_wl[:2]: np.nan} for u, v, k, edata in
                                    graph.edges.data(keys=True) if 'geometry' not in edata})

            # Add the hazard values to the edges that do have a geometry
            gdf = gpd.GeoDataFrame({'geometry': [edata['geometry'] for u, v, k, edata in edges_geoms]})
            tqdm.pandas(desc="Graph hazard overlay with " + hn)
            flood_stats = gdf.geometry.progress_apply(lambda x: zonal_stats(x, str(self.hazard_files['tif'][i]),
                                                                            all_touched=True,
                                                                            stats=f"{self.aggregate_wl}"))

            try:
                flood_stats = flood_stats.apply(lambda x: x[0][self.aggregate_wl] if x[0][self.aggregate_wl] else 0)
                nx.set_edge_attributes(graph,
                                       {(edges[0], edges[1], edges[2]): {rn + '_' + self.aggregate_wl[:2]: x} for
                                        x, edges in
                                        zip(flood_stats, edges_geoms)})
            except:
                logging.warning(
                    "No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'.")

            # Get the fraction of the road that is intersecting with the hazard
            tqdm.pandas(desc="Graph fraction with hazard overlay with " + hn)
            graph_fraction_flooded = gdf.geometry.progress_apply(
                lambda x: fraction_flooded(x, str(self.hazard_files['tif'][i])))
            graph_fraction_flooded = graph_fraction_flooded.fillna(0)
            nx.set_edge_attributes(graph,
                                   {(edges[0], edges[1], edges[2]): {rn + '_fr': x} for x, edges in
                                    zip(graph_fraction_flooded, edges_geoms)})

        return graph

    def overlay_hazard_shp_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the hazard shapefile over the road segments GeoDataFrame.

        Args:
            gdf (GeoDataFrame): the network geodataframe that should be overlayed with the hazard shapefile(s)

        Returns:
            gdf (GeoDataFrame): the network geodataframe with hazard shapefile(s) data joined

        The gdf is reprojected to the hazard shapefile if necessary.
        """
        hfns = self.config['hazard']['hazard_field_name']
        gdf_crs_original = gdf.crs

        for i, (hn, rn, hfn) in enumerate(zip(self.hazard_names, self.ra2ce_names, hfns)):
            gdf_hazard = gpd.read_file(str(self.hazard_files['shp'][i]))

            if gdf.crs != gdf_hazard.crs:
                gdf = gdf.to_crs(gdf_hazard.crs)

            gdf = gpd.sjoin(gdf, gdf_hazard[[hfn, 'geometry']], how='left')
            gdf.rename(columns={hfn: rn + '_' + self.aggregate_wl[:2]}, inplace=True)

        if gdf.crs != gdf_crs_original:
            gdf = gdf.to_crs(gdf_crs_original)

        return gdf

    def overlay_hazard_shp_graph(self, graph: nx.Graph) -> nx.Graph:
        """Overlays the hazard shapefile over the road segments NetworkX graph.

        Args:
            graph (NetworkX graph): The graph that should be overlayed with the hazard shapefile(s)

        Returns:
            graph (NetworkX graph): The graph with hazard shapefile(s) data joined
        """
        # TODO check if the CRS of the graph and shapefile match

        hfns = self.config['hazard']['hazard_field_name']

        for i, (hn, rn, hfn) in enumerate(zip(self.hazard_names, self.ra2ce_names, hfns)):
            gdf = gpd.read_file(str(self.hazard_files['shp'][i]))
            spatial_index = gdf.sindex

            for u, v, k, edata in graph.edges.data(keys=True):
                if 'geometry' in edata:
                    possible_matches_index = list(spatial_index.intersection(edata['geometry'].bounds))
                    possible_matches = gdf.iloc[possible_matches_index]
                    precise_matches = possible_matches[possible_matches.intersects(edata['geometry'])]

                    if not precise_matches.empty:
                        if self.aggregate_wl == 'max':
                            graph[u][v][k][rn + '_' + self.aggregate_wl[:2]] = precise_matches[hfn].max()
                        if self.aggregate_wl == 'min':
                            graph[u][v][k][rn + '_' + self.aggregate_wl[:2]] = precise_matches[hfn].min()
                        if self.aggregate_wl == 'mean':
                            graph[u][v][k][rn + '_' + self.aggregate_wl[:2]] = precise_matches[hfn].mean()
                    else:
                        graph[u][v][k][rn + '_' + self.aggregate_wl[:2]] = 0
                else:
                    graph[u][v][k][rn + '_' + self.aggregate_wl[:2]] = 0

        return graph

    def od_hazard_intersect(self, graph: nx.Graph) -> nx.Graph:
        """Overlays the origin and destination locations and edges with the hazard maps

        Args:
            graph (NetworkX graph): The origin-destination graph that should be overlayed with the hazard raster(s)

        Returns:
            graph (NetworkX graph): The origin-destination graph hazard raster(s) data joined to both the origin- and
            destination nodes and the edges.
        """
        from tqdm import tqdm

        ## Intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        # Verify the graph type (networkx)
        assert type(graph).__module__.split('.')[0] == 'networkx'
        extent_graph = get_graph_edges_extent(graph)

        # Get all node geometries
        od_nodes = [(n, ndata) for n, ndata in graph.nodes.data() if 'od_id' in ndata]
        od_ids = [n[0] for n in od_nodes]

        # Get all edge geometries
        edges_geoms = [(u, v, k, edata) for u, v, k, edata in graph.edges.data(keys=True) if 'geometry' in edata]

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            extent = get_extent(gdal.Open(str(self.hazard_files['tif'][i])))
            extent_hazard = (extent['minX'], extent['maxX'], extent['minY'], extent['maxY'])

            if bounds_intersect_2d(extent_graph, extent_hazard):
                pass

            else:
                logging.info("Raster extent: {}, Graph extent: {}".format(extent, extent_graph))
                raise ValueError(
                    "The hazard raster and the graph geometries do not overlap, check projection")

            # Read the hazard values at the nodes and write to the nodes.
            gdf = gpd.GeoDataFrame({'geometry': [ndata['geometry'] for n, ndata in od_nodes]})
            tqdm.pandas(desc='Destinations hazard overlay with ' + hn)
            flood_stats = gdf.geometry.progress_apply(lambda x: point_query(x, str(self.hazard_files['tif'][i])))

            flood_stats = flood_stats.apply(lambda x: x[0] if x[0] else 0)
            attribute_dict = {od: {rn + '_' + self.aggregate_wl[:2]: wl} for od, wl in zip(od_ids, flood_stats)}
            nx.set_node_attributes(graph, attribute_dict)

            # Read the hazard values at the edges and write to the edges.
            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(graph,
                                   {(u, v, k): {rn + '_' + self.aggregate_wl[:2]: np.nan} for u, v, k, edata in
                                    graph.edges.data(keys=True) if 'geometry' not in edata})

            # Add the hazard values to the edges that do have a geometry
            gdf = gpd.GeoDataFrame({'geometry': [edata['geometry'] for u, v, k, edata in edges_geoms]})
            tqdm.pandas(desc='OD graph hazard overlay with ' + hn)
            flood_stats = gdf.geometry.progress_apply(lambda x: zonal_stats(x, str(self.hazard_files['tif'][i]),
                                                                            all_touched=True,
                                                                            stats=f"{self.aggregate_wl}"))

            try:
                flood_stats = flood_stats.fillna(0)
                nx.set_edge_attributes(graph,
                                       {(edges[0], edges[1], edges[2]): {
                                           rn + '_' + self.aggregate_wl[:2]: x[0][self.aggregate_wl]} for x, edges in
                                           zip(flood_stats, edges_geoms)})
            except:
                logging.warning(
                    "No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'.")

            # Get the fraction of the road that is intersecting with the hazard
            tqdm.pandas(desc='OD graph fraction with hazard overlay with ' + hn)
            graph_fraction_flooded = gdf.geometry.progress_apply(
                lambda x: fraction_flooded(x, str(self.hazard_files['tif'][i])))
            graph_fraction_flooded = graph_fraction_flooded.fillna(0)
            nx.set_edge_attributes(graph,
                                   {(edges[0], edges[1], edges[2]): {rn + '_fr': x} for x, edges in
                                    zip(graph_fraction_flooded, edges_geoms)})

        return graph

    def point_hazard_intersect(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the point locations with hazard maps

        Args:
            gdf (GeoDataFrame): the point geodataframe that should be overlayed with the hazard raster(s)
        Returns:
            gdf (GeoDataFrame): the point geodataframe with hazard raster(s) data joined
        """
        from tqdm import tqdm

        ## Intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Read the hazard values at the nodes and write to the nodes.
            tqdm.pandas(desc='Potentially isolated locations hazard overlay with ' + hn)
            flood_stats = gdf.geometry.progress_apply(lambda x: point_query(x, str(self.hazard_files['tif'][i])))
            gdf[rn + '_' + self.aggregate_wl[:2]] = flood_stats.apply(lambda x: x[0] if x[0] else 0)

        return gdf

    def join_hazard_table_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs.

        Args:

        Returns:

        """
        for haz in self.hazard_files['table']:
            if haz.suffix in ['.csv']:
                gdf = self.join_table(gdf, haz)
        return gdf

    def join_hazard_table_graph(self, graph: nx.Graph) -> nx.Graph:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs.

        Args:

        Returns:

        """
        gdf, gdf_nodes = graph_to_gdf(graph, save_nodes=True)
        gdf = self.join_hazard_table_gdf(gdf)

        # TODO: Check if the graph is created again correctly.
        graph = graph_from_gdf(gdf, gdf_nodes)
        return graph

    def join_table(self, graph: nx.Graph, hazard: str) -> nx.Graph:
        df = pd.read_csv(hazard)
        df = df[self.config['hazard']['hazard_field_name']]
        graph = graph.merge(df,
                            how='left',
                            left_on=self.config['network']['file_id'],
                            right_on=self.config['hazard']['hazard_id'])

        graph.rename(columns={
            self.config['hazard']['hazard_field_name']: [n[:-3] for n in self.hazard_name_table['RA2CE name']][0]},
                     inplace=True)  # Check if this is the right name
        return graph

    def get_hazard_name_table(self) -> pd.DataFrame:
        agg_types = ['maximum', 'minimum', 'average', 'fraction of network segment impacted by hazard']
        _hazard_map_config = self.config['hazard']['hazard_map']
        df = pd.DataFrame()
        df[['File name', 'Aggregation method']] = [(haz.stem, agg_type) for haz in _hazard_map_config for agg_type in
                                                   agg_types]
        if all(['RP' in haz.stem for haz in _hazard_map_config]):
            # Return period hazard maps are used
            # TODO: now it is assumed that there is a flood event, this should be made flexible
            rps = [haz.stem.split('RP_')[-1].split('_')[0] for haz in _hazard_map_config]
            df['RA2CE name'] = ['F_' + 'RP' + rp + '_' + agg_type[:2] for rp in rps for agg_type in agg_types]
        else:
            # Event hazard maps are used
            # TODO: now it is assumed that there is a flood event, this should be made flexible
            df['RA2CE name'] = ['F_' + 'EV' + str(i + 1) + '_' + agg_type[:2] for i in range(len(_hazard_map_config))
                                for agg_type in agg_types]
        df['Full path'] = [haz for haz in _hazard_map_config for _ in agg_types]
        return df

    def get_hazard_files(self):
        """Sorts the hazard files into tif, shp, and csv/json

        This function returns nothing but creates a dict self.hazard_files of hazard files sorted per type.
        {key = hazard file type (tif / shp / table (csv/json) : value = list of file paths}
        """
        _hazard_maps = self.config['hazard']['hazard_map']
        hazards_tif = [haz for haz in _hazard_maps if haz.suffix == '.tif']
        hazards_shp = [haz for haz in _hazard_maps if haz.suffix == '.shp']
        hazards_table = [haz for haz in _hazard_maps if haz.suffix in ['.csv', '.json']]

        self.hazard_files['tif'] = hazards_tif
        self.hazard_files['shp'] = hazards_shp
        self.hazard_files['table'] = hazards_table

    def get_hazard_intersect_geodataframe_tif(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        """Logic to find the right hazard overlay function for the input to_overlay.

        Args:
            to_overlay (GeoDataFrame or NetworkX graph): Data that needs to be overlayed with a or multiple hazard maps.

        Returns:
            to_overlay (GeoDataFrame or NetworkX graph): The same data as input but with hazard values.

        The hazard file paths are in self.hazard_files.
        """
        start = time.time()
        to_overlay = self.overlay_hazard_raster_gdf(to_overlay)
        end = time.time()
        logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_networkx_tif(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        start = time.time()
        to_overlay = self.overlay_hazard_raster_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_geodataframe_shp(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_gdf(to_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_networkx_shp(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_geodataframe_table(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        start = time.time()
        to_overlay = self.join_hazard_table_gdf(to_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_networkx_table(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]):
        start = time.time()
        to_overlay = self.join_hazard_table_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def hazard_intersect(self, to_overlay: Union[gpd.GeoDataFrame, nx.Graph]) -> Union[gpd.GeoDataFrame, nx.Graph]:
        """Handler function that chooses the right function for overlaying the network with the hazard data."""
        if (self.hazard_files['tif']) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_tif(to_overlay)
        elif (self.hazard_files['tif']) and (type(to_overlay).__module__.split('.')[0] == 'networkx'):
            to_overlay = self.get_hazard_intersect_networkx_tif(to_overlay)
        elif (self.hazard_files['shp']) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_shp(to_overlay)
        elif (self.hazard_files['shp']) and (type(to_overlay).__module__.split('.')[0] == 'networkx'):
            to_overlay = self.get_hazard_intersect_networkx_shp(to_overlay)
        elif (self.hazard_files['table']) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_table(to_overlay)
        elif (self.hazard_files['table']) and (type(to_overlay).__module__.split('.')[0] == 'networkx'):
            to_overlay = self.get_hazard_intersect_networkx_table(to_overlay)
        else:
            logging.warning(f"The overlay of the combination of hazard file(s) '{self.hazard_files}' and network type '{type(to_overlay)}' is not available."
                            f"Please check your input data.")

        return to_overlay

    def create(self):
        """ Overlays the different possible graph objects with the hazard data

        Arguments:
            None
            (implicit) : (self.graphs) : dictionary with the graph names as keys, and values the graphs
                        keys: ['base_graph', 'base_network', 'origins_destinations_graph']

        Returns:
            self.graph : same dictionary, but with new keys _hazard, which are copies of the graphs but with hazard data

        Effect:
            write all the objects

        """
        to_save = ['pickle'] if not self.config['network']['save_shp'] else ['pickle', 'shp']

        if self.files['base_graph'] is None and self.files['origins_destinations_graph'] is None:
            logging.warning("Either a base graph or OD graph is missing to intersect the hazard with. "
                            "Check your network folder.")

        # Iterate over the three graph/network types to load the file if necessary (when not yet loaded in memory).
        for input_graph in ['base_graph', 'base_network', 'origins_destinations_graph']:
            file_path = self.files[input_graph]

            if file_path is not None or self.graphs[input_graph] is not None:
                if self.graphs[input_graph] is None and input_graph != 'base_network':
                    self.graphs[input_graph] = read_gpickle(file_path)
                elif self.graphs[input_graph] is None and input_graph == 'base_network':
                    self.graphs[input_graph] = gpd.read_feather(file_path)

        #### Step 1: hazard overlay of the base graph (NetworkX) ###
        if (self.graphs['base_graph'] is not None) and (self.files['base_graph_hazard'] is None):
            graph = self.graphs['base_graph']

            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self.config['hazard']['hazard_crs'])
            graph_crs = pyproj.CRS.from_user_input(
                "EPSG:4326")  # this is WGS84, TODO: Make flexible by including in the network ini

            if hazard_crs != graph_crs:  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning("""Hazard crs {} and graph crs {} are inconsistent, 
                                              we try to reproject the graph crs""".format(hazard_crs, graph_crs))
                extent_graph = get_graph_edges_extent(graph)
                logging.info('Graph extent before reprojecting: {}'.format(extent_graph))
                graph_reprojected = reproject_graph(graph, graph_crs, hazard_crs)
                extent_graph_reprojected = get_graph_edges_extent(graph_reprojected)
                logging.info('Graph extent after reprojecting: {}'.format(extent_graph_reprojected))

                # Do the actual hazard intersect
                base_graph_hazard_reprojected = self.hazard_intersect(graph_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = nx.get_edge_attributes(graph, 'geometry')
                base_graph_hazard = base_graph_hazard_reprojected.copy()
                nx.set_edge_attributes(base_graph_hazard, original_geometries, 'geometry')
                self.graphs['base_graph_hazard'] = base_graph_hazard.copy()
                del graph_reprojected
                del base_graph_hazard_reprojected
                del base_graph_hazard
            else:
                self.graphs['base_graph_hazard'] = self.hazard_intersect(
                    graph)

            # Save graphs/network with hazard
            self.files['base_graph_hazard'] = save_network(
                self.graphs['base_graph_hazard'], self.config['static'] / 'output_graph',
                'base_graph_hazard', types=to_save)
        else:
            try:
                # Try to find the base graph hazard file
                self.graphs['base_graph_hazard'] = read_gpickle(
                    self.config['static'] / 'output_graph' / 'base_graph_hazard.p')
            except FileNotFoundError:
                # File not found
                logging.warning(
                    f"Base graph hazard file not found at {self.config['static'] / 'output_graph' / 'base_graph_hazard.p'}")
                pass

        #### Step 2: hazard overlay of the origins_destinations (NetworkX) ###
        if (self.config['origins_destinations']['origins'] is not None) and (
                self.config['origins_destinations']['origins'] is not None) \
                and (self.graphs['origins_destinations_graph'] is not None) and (
                self.files['origins_destinations_graph_hazard'] is None):
            graph = self.graphs['origins_destinations_graph']

            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self.config['hazard']['hazard_crs'])
            graph_crs = pyproj.CRS.from_user_input(
                "EPSG:4326")  # this is WGS84, TODO: Make flexible by including in the network ini

            if hazard_crs != graph_crs:  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning("""Hazard crs {} and graph crs {} are inconsistent, 
                                              we try to reproject the graph crs""".format(hazard_crs, graph_crs))
                extent_graph = get_graph_edges_extent(graph)
                logging.info('Graph extent before reprojecting: {}'.format(extent_graph))
                graph_reprojected = reproject_graph(graph, graph_crs, hazard_crs)
                extent_graph_reprojected = get_graph_edges_extent(graph_reprojected)
                logging.info('Graph extent after reprojecting: {}'.format(extent_graph_reprojected))

                # Do the actual hazard intersect
                od_graph_hazard_reprojected = self.od_hazard_intersect(graph_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = nx.get_edge_attributes(graph, 'geometry')
                od_graph_hazard = od_graph_hazard_reprojected.copy()
                nx.set_edge_attributes(od_graph_hazard, original_geometries, 'geometry')
                self.graphs['origins_destinations_graph_hazard'] = od_graph_hazard.copy()
                del graph_reprojected
                del od_graph_hazard_reprojected
                del od_graph_hazard

            else:
                self.graphs['origins_destinations_graph_hazard'] = self.od_hazard_intersect(
                    graph)

            # Save graphs/network with hazard
            self.files['origins_destinations_graph_hazard'] = save_network(
                self.graphs['origins_destinations_graph_hazard'], self.config['static'] / 'output_graph',
                'origins_destinations_graph_hazard', types=to_save)

        #### Step 3: iterate overlay of the GeoPandas Dataframe (if any) ###
        if (self.graphs['base_network'] is not None) and (self.files['base_network_hazard'] is None):
            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self.config['hazard']['hazard_crs'])
            gdf_crs = pyproj.CRS.from_user_input(self.graphs['base_network'].crs)

            if hazard_crs != gdf_crs:  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning("""Hazard crs {} and gdf crs {} are inconsistent, 
                                              we try to reproject the gdf crs""".format(hazard_crs, gdf_crs))
                extent_gdf = self.graphs['base_network'].total_bounds
                logging.info('Gdf extent before reprojecting: {}'.format(extent_gdf))
                gdf_reprojected = self.graphs['base_network'].copy().to_crs(hazard_crs)
                extent_gdf_reprojected = gdf_reprojected.total_bounds
                logging.info('Gdf extent after reprojecting: {}'.format(extent_gdf_reprojected))

                # Do the actual hazard intersect
                gdf_reprojected = self.hazard_intersect(gdf_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = self.graphs['base_network']['geometry']
                gdf_reprojected['geometry'] = original_geometries
                self.graphs['base_network_hazard'] = gdf_reprojected.copy()
                del gdf_reprojected
            else:
                self.graphs['base_network_hazard'] = self.hazard_intersect(self.graphs['base_network'])

            # Save graphs/network with hazard
            self.files['base_network_hazard'] = save_network(
                self.graphs['base_network_hazard'], self.config['static'] / 'output_graph',
                'base_network_hazard', types=to_save)
        else:
            try:
                # Try to find the base network hazard file
                self.graphs['base_network_hazard'] = gpd.read_feather(
                    self.config['static'] / 'output_graph' / 'base_network_hazard.feather')
            except FileNotFoundError:
                # File not found
                logging.warning(
                    f"Base network hazard file not found at {self.config['static'] / 'output_graph' / 'base_network_hazard.feather'}")
                pass

        if 'isolation' in self.config:
            locations = gpd.read_file(self.config['isolation']['locations'][0])
            locations['i_id'] = locations.index
            locations_crs = pyproj.CRS.from_user_input(locations.crs)
            hazard_crs = pyproj.CRS.from_user_input(self.config['hazard']['hazard_crs'])

            if hazard_crs != locations_crs:  # Temporarily reproject the locations to the CRS of the hazard
                logging.warning("""Hazard crs {} and location crs {} are inconsistent, 
                                               we try to reproject the location crs""".format(hazard_crs,
                                                                                              locations_crs))
                extent_locations = locations.total_bounds
                logging.info('Gdf extent before reprojecting: {}'.format(extent_locations))
                locations_reprojected = locations.copy().to_crs(hazard_crs)
                extent_locations_reprojected = locations_reprojected.total_bounds
                logging.info('Gdf extent after reprojecting: {}'.format(extent_locations_reprojected))

                # Do the actual hazard intersect
                locations_reprojected = self.point_hazard_intersect(locations_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = locations['geometry']
                locations_reprojected['geometry'] = original_geometries
                locations = locations_reprojected.copy()
                del locations_reprojected
            else:
                locations = self.point_hazard_intersect(locations)

            save_network(locations, self.config['static'] / 'output_graph', 'locations_hazard')

        # Save the hazard name bookkeeping table.
        self.hazard_name_table.to_excel(self.config['output'] / 'hazard_names.xlsx', index=False)

        return self.graphs
