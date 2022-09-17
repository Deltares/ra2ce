# -*- coding: utf-8 -*-
"""
Created on 26-7-2021
"""

from typing import Tuple, Union

# external modules
import pyproj
from osmnx.graph import graph_from_xml

# local modules
from ra2ce.graph.networks_utils import *
from ra2ce.io.readers import GraphPickleReader


class Network:
    """Network in GeoDataFrame or NetworkX format.

    Networks can be created from shapefiles, OSM PBF files, can be downloaded from OSM online or can be loaded from
    feather or gpickle files. Origin-destination nodes can be added.

    Attributes:
        config: A dictionary with the configuration details on how to create and adjust the network.
    """

    def __init__(self, config, files):
        # General
        self.config = config
        self.output_path = config["static"] / "output_graph"
        if not self.output_path.is_dir():
            self.output_path.mkdir(parents=True)
        # Network
        self.base_graph_crs = None  # Initiate variable
        self.base_network_crs = None  # Initiate variable

        # Origins and destinations
        self.origins = config["origins_destinations"]["origins"]
        self.destinations = config["origins_destinations"]["destinations"]
        self.origins_names = config["origins_destinations"]["origins_names"]
        self.destinations_names = config["origins_destinations"]["destinations_names"]
        self.id_name_origin_destination = config["origins_destinations"][
            "id_name_origin_destination"
        ]
        try:
            self.region = (
                config["static"] / "network" / config["origins_destinations"]["region"]
            )
            self.region_var = config["origins_destinations"]["region_var"]
        except:
            self.region = None
            self.region_var = None

        # Cleanup
        self.snapping = config["cleanup"]["snapping_threshold"]
        self.segmentation_length = config["cleanup"]["segmentation_length"]

        # files
        self.files = files

    def network_shp(
        self, crs: int = 4326
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a (graph) network from a shapefile.

        Returns the same geometries for the network (GeoDataFrame) as for the graph (NetworkX graph), because
        it is assumed that the user wants to keep the same geometries as their shapefile input.

        Args:
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            graph_complex (NetworkX graph): The resulting graph.
            edges_complex (GeoDataFrame): The resulting network.
        """
        # Make a pyproj CRS from the EPSG code
        crs = pyproj.CRS.from_user_input(crs)

        lines = self.read_merge_shp()
        logging.info(
            "Function [read_merge_shp]: executed with {} {}".format(
                self.config["network"]["primary_file"],
                self.config["network"]["diversion_file"],
            )
        )

        # Multilinestring to linestring
        # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
        # The list of fid's is reduced by the fid's that are not anymore in the merged lines
        aadt_names = None
        edges, lines_merged = merge_lines_automatic(
            lines, self.config["network"]["file_id"], aadt_names, crs
        )
        logging.info(
            "Function [merge_lines_shpfiles]: executed with properties {}".format(
                list(edges.columns)
            )
        )

        edges, id_name = gdf_check_create_unique_ids(
            edges, self.config["network"]["file_id"]
        )

        if self.snapping is not None:
            edges = snap_endpoints_lines(edges, self.snapping, id_name, tolerance=1e-7)
            logging.info(
                "Function [snap_endpoints_lines]: executed with threshold = {}".format(
                    self.snapping
                )
            )

        # merge merged lines if there are any merged lines
        if not lines_merged.empty:
            # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
            lines_merged.to_file(
                os.path.join(
                    self.output_path,
                    "{}_lines_that_merged.shp".format(self.config["project"]["name"]),
                )
            )
            logging.info(
                "Function [edges_to_shp]: saved at {}".format(
                    os.path.join(
                        self.output_path,
                        "{}_lines_that_merged".format(self.config["project"]["name"]),
                    )
                )
            )

        # Get the unique points at the end of lines and at intersections to create nodes
        nodes = create_nodes(edges, crs, self.config["cleanup"]["ignore_intersections"])
        logging.info("Function [create_nodes]: executed")

        if self.snapping is not None:
            # merged lines may be updated when new nodes are created which makes a line cut in two
            edges = cut_lines(edges, nodes, id_name, tolerance=1e-4)
            nodes = create_nodes(
                edges, crs, self.config["cleanup"]["ignore_intersections"]
            )
            logging.info("Function [cut_lines]: executed")

        # create tuples from the adjecent nodes and add as column in geodataframe
        edges_complex = join_nodes_edges(nodes, edges, id_name)
        edges_complex.crs = crs  # set the right CRS

        # Create networkx graph from geodataframe
        graph_complex = graph_from_gdf(edges_complex, nodes, node_id="node_fid")
        logging.info(
            "Function [graph_from_gdf]: executing, with '{}_resulting_network.shp'".format(
                self.config["project"]["name"]
            )
        )

        if self.segmentation_length is not None:
            edges_complex = Segmentation(edges_complex, self.segmentation_length)
            edges_complex = edges_complex.apply_segmentation()
            if edges_complex.crs is None:  # The CRS might have dissapeared.
                edges_complex.crs = crs  # set the right CRS

        self.base_graph_crs = pyproj.CRS.from_user_input(crs)
        self.base_network_crs = pyproj.CRS.from_user_input(crs)

        # Exporting complex graph because the shapefile should be kept the same as much as possible.
        return graph_complex, edges_complex

    def network_osm_pbf_DEPRECIATED(
        self, crs=4326
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a network from an OSM PBF file.

        WARNING: THIS FUNCTION IS DEPRECIATED SINCE 10/8/2022, WHEN KEES MADE A NEW OSM PBF IMPORT USING
                THE TRAILS PACKAGE.

        Args:
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            G_simple (NetworkX graph): Simplified graph (for use in the indirect analyses).
            G_complex_edges (GeoDataFrame): Complex graph (for use in the direct analyses).
        """
        road_types = (
            self.config["network"]["road_types"].lower().replace(" ", " ").split(",")
        )

        input_path = self.config["static"] / "network"
        executables_path = Path(__file__).parents[1] / "executables"
        osm_convert_exe = executables_path / "osmconvert64.exe"
        osm_filter_exe = executables_path / "osmfilter.exe"
        assert osm_convert_exe.exists() and osm_filter_exe.exists()

        pbf_file = input_path / self.config["network"]["primary_file"]
        o5m_path = input_path / self.config["network"]["primary_file"].replace(
            ".pbf", ".o5m"
        )
        o5m_filtered_path = input_path / self.config["network"]["primary_file"].replace(
            ".pbf", "_filtered.o5m"
        )

        # Todo: check what excacly these functions do, and if this is always what we want
        if o5m_filtered_path.exists():
            logging.info(
                "filtered o5m path already exists: {}".format(o5m_filtered_path)
            )
        elif o5m_path.exists():
            filter_osm(osm_filter_exe, o5m_path, o5m_filtered_path, tags=road_types)
            logging.info("filtered o5m pbf, created: {}".format(o5m_path))
        else:
            convert_osm(osm_convert_exe, pbf_file, o5m_path)
            filter_osm(osm_filter_exe, o5m_path, o5m_filtered_path, tags=road_types)
            logging.info(
                "Converted and filtered osm.pbf to o5m, created: {}".format(o5m_path)
            )

        logging.info("Start reading graph from o5m...")
        # Todo: make sure that bidirectionality is inferred from the settings, similar for other settings
        graph_complex = graph_from_xml(
            o5m_filtered_path, bidirectional=False, simplify=False, retain_all=False
        )

        # Create 'graph_simple'
        graph_simple, graph_complex, link_tables = create_simplified_graph(
            graph_complex
        )

        # Create 'edges_complex', convert complex graph to geodataframe
        logging.info("Start converting the graph to a geodataframe")
        edges_complex, node_complex = graph_to_gdf(graph_complex)
        logging.info("Finished converting the graph to a geodataframe")

        # Save the link tables linking complex and simple IDs
        save_linking_tables(
            self.config["static"] / "output_graph", link_tables[0], link_tables[1]
        )

        if self.segmentation_length is not None:
            edges_complex = Segmentation(edges_complex, self.segmentation_length)
            edges_complex = edges_complex.apply_segmentation()
            if edges_complex.crs is None:  # The CRS might have dissapeared.
                edges_complex.crs = crs  # set the right CRS

        self.base_graph_crs = pyproj.CRS.from_user_input(crs)
        self.base_network_crs = pyproj.CRS.from_user_input(crs)

        return graph_simple, edges_complex

    def network_trails_import(
        self, crs: int = 4326
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a network which has been prepared in the TRAILS package

        #Todo: we might later simply import the whole trails code as a package, and directly use these functions
        #Todo: because TRAILS is still in beta version we better wait with that untill the first stable version is
        # released

        Returns:
            graph_simple (NetworkX graph): Simplified graph (for use in the indirect analyses).
            complex_edges (GeoDataFrame): Complex graph (for use in the direct analyses).
        """

        logging.info(
            "TRAILS importer: Reads the provided primary edge file: {}, assumes there also is a_nodes file".format(
                self.config["network"]["primary_file"]
            )
        )
        edges = pd.read_pickle(
            self.config["static"] / "network" / self.config["network"]["primary_file"]
        )
        corresponding_node_file = (
            self.config["static"]
            / "network"
            / self.config["network"]["primary_file"].replace("edges", "nodes")
        )
        assert corresponding_node_file.exists()
        nodes = pd.read_pickle(
            corresponding_node_file
        )  # Todo: Throw exception if nodes file is not present

        logging.info("TRAILS importer: start generating graph")
        # tempfix to rename columns
        edges = edges.rename({"from_id": "node_A", "to_id": "node_B"}, axis="columns")
        node_id = "id"
        graph_simple = graph_from_gdf(edges, nodes, name="network", node_id=node_id)

        logging.info("TRAILS importer: graph generating was succesfull.")
        logging.warning(
            "RA2CE will not clean-up your graph, assuming that it is already done in TRAILS"
        )

        if self.segmentation_length is not None:
            to_segment = Segmentation(edges, self.segmentation_length)
            edges_simple_segmented = to_segment.apply_segmentation()
            if edges_simple_segmented.crs is None:  # The CRS might have dissapeared.
                edges_simple_segmented.crs = crs  # set the right CRS
                edges_complex = edges_simple_segmented

        else:
            edges_complex = edges

        graph_complex = graph_simple  # NOTE THAT DIFFERENCE
        # BETWEEN SIMPLE AND COMPLEX DOES NOT EXIST WHEN IMPORTING WITH TRAILS

        # Todo: better control over metadata in trails
        # Todo: better control over where things are saved in the pipeline

        return graph_complex, edges_complex

    def network_osm_download(self) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Creates a network from a polygon by downloading via the OSM API in the extent of the polygon.

        Returns:
            graph_simple (NetworkX graph): Simplified graph (for use in the indirect analyses).
            complex_edges (GeoDataFrame): Complex graph (for use in the direct analyses).
        """
        poly_dict = read_geojson(
            self.config["network"]["polygon"][0]
        )  # It can only read in one geojson
        poly = geojson_to_shp(poly_dict)

        if not self.config["network"]["road_types"]:
            # The user specified only the network type.
            graph_complex = osmnx.graph_from_polygon(
                polygon=poly,
                network_type=self.config["network"]["network_type"],
                simplify=False,
                retain_all=True,
            )
        elif not self.config["network"]["network_type"]:
            # The user specified only the road types.
            cf = '["highway"~"{}"]'.format(
                self.config["network"]["road_types"].replace(",", "|")
            )
            graph_complex = osmnx.graph_from_polygon(
                polygon=poly, custom_filter=cf, simplify=False, retain_all=True
            )
        else:
            # The user specified the network type and road types.
            cf = '["highway"~"{}"]'.format(
                self.config["network"]["road_types"].replace(",", "|")
            )
            graph_complex = osmnx.graph_from_polygon(
                polygon=poly,
                network_type=self.config["network"]["network_type"],
                custom_filter=cf,
                simplify=False,
                retain_all=True,
            )

        logging.info(
            "graph downloaded from OSM with {:,} nodes and {:,} edges".format(
                len(list(graph_complex.nodes())), len(list(graph_complex.edges()))
            )
        )

        # Create 'graph_simple'
        graph_simple, graph_complex, link_tables = create_simplified_graph(
            graph_complex
        )

        # Create 'edges_complex', convert complex graph to geodataframe
        logging.info("Start converting the graph to a geodataframe")
        edges_complex, node_complex = graph_to_gdf(graph_complex)
        logging.info("Finished converting the graph to a geodataframe")

        # Save the link tables linking complex and simple IDs
        save_linking_tables(
            self.config["static"] / "output_graph", link_tables[0], link_tables[1]
        )

        # If the user wants to use undirected graphs, turn into an undirected graph (default).
        if not self.config["network"]["directed"]:
            if type(graph_simple) == nx.classes.multidigraph.MultiDiGraph:
                graph_simple = graph_simple.to_undirected()

        # No segmentation required, the non-simplified road segments from OSM are already small enough

        self.base_graph_crs = pyproj.CRS.from_user_input(
            "EPSG:4326"
        )  # Graphs from OSM download are always in this CRS.
        self.base_network_crs = pyproj.CRS.from_user_input(
            "EPSG:4326"
        )  # Graphs from OSM download are always in this CRS.

        return graph_simple, edges_complex

    def add_od_nodes(
        self, graph: nx.classes.graph.Graph, crs: pyproj.CRS
    ) -> nx.classes.graph.Graph:
        """Adds origins and destinations nodes from shapefiles to the graph.

        Args:
            graph (NetworkX graph): the NetworkX graph to which OD nodes should be added
            crs (int): the EPSG number of the coordinate reference system that is used

        Returns:
            graph (NetworkX graph): the NetworkX graph with OD nodes
        """
        from ra2ce.graph.origins_destinations import (
            add_od_nodes,
            create_OD_pairs,
            read_OD_files,
        )

        name = "origin_destination_table"

        # Add the origin/destination nodes to the network
        ods = read_OD_files(
            self.origins,
            self.origins_names,
            self.destinations,
            self.destinations_names,
            self.id_name_origin_destination,
            self.config["origins_destinations"]["origin_count"],
            crs,
            self.region,
            self.region_var,
        )

        ods = create_OD_pairs(ods, graph)
        ods.crs = crs

        # Save the OD pairs (GeoDataFrame) as pickle
        ods.to_feather(
            self.config["static"] / "output_graph" / (name + ".feather"), index=False
        )
        logging.info(
            f"Saved {name + '.feather'} in {self.config['static'] / 'output_graph'}."
        )

        # Save the OD pairs (GeoDataFrame) as shapefile
        if self.config["network"]["save_shp"]:
            ods_path = self.config["static"] / "output_graph" / (name + ".shp")
            ods.to_file(ods_path, index=False)
            logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        graph = add_od_nodes(graph, ods, crs)

        return graph

    def generate_origins_from_raster(self):
        """Adds origins and destinations nodes from shapefiles to the graph."""
        from ra2ce.graph.origins_destinations import origins_from_raster

        out_fn = origins_from_raster(
            self.config["static"] / "network",
            self.config["network"]["polygon"],
            self.origins[0],
        )

        return out_fn

    def read_merge_shp(self, crs_: int = 4326) -> gpd.GeoDataFrame:
        """Imports shapefile(s) and saves attributes in a pandas dataframe.

        Args:
            crs_ (int): the EPSG number of the coordinate reference system that is used
        Returns:
            lines (list of shapely LineStrings): full list of linestrings
            properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
        """

        # read shapefiles and add to list with path
        if isinstance(self.config["network"]["primary_file"], str):
            shapefiles_analysis = [
                self.config["static"] / "network" / shp
                for shp in self.config["network"]["primary_file"].split(",")
            ]
        if isinstance(self.config["network"]["diversion_file"], str):
            shapefiles_diversion = [
                self.config["static"] / "network" / shp
                for shp in self.config["network"]["diversion_file"].split(",")
            ]

        # concatenate all shapefile into one geodataframe and set analysis to 1 or 0 for diversions
        lines = [gpd.read_file(shp) for shp in shapefiles_analysis]
        # for

        # check_crs_gdf(, crs_)
        if isinstance(self.config["network"]["diversion_file"], str):
            lines.extend(
                [
                    check_crs_gdf(gpd.read_file(shp), crs_)
                    for shp in shapefiles_diversion
                ]
            )
        lines = pd.concat(lines)

        lines.crs = crs_

        # append the length of the road stretches
        lines["length"] = lines["geometry"].apply(lambda x: line_length(x, lines.crs))

        if lines["geometry"].apply(lambda row: isinstance(row, MultiLineString)).any():
            for line in lines.loc[
                lines["geometry"].apply(lambda row: isinstance(row, MultiLineString))
            ].iterrows():
                if len(linemerge(line[1].geometry)) > 1:
                    logging.warning(
                        "Edge with {} = {} is a MultiLineString, which cannot be merged to one line. Check this part.".format(
                            self.config["network"]["file_id"],
                            line[1][self.config["network"]["file_id"]],
                        )
                    )

        logging.info(
            "Shapefile(s) loaded with attributes: {}.".format(
                list(lines.columns.values)
            )
        )  # fill in parameter names

        return lines

    def get_avg_speed(self, G: nx.classes.graph.Graph) -> nx.classes.graph.Graph:
        if all(["length" in e for u, v, e in G.edges.data()]) and any(
            ["maxspeed" in e for u, v, e in G.edges.data()]
        ):
            # Add time weighing - Define and assign average speeds; or take the average speed from an existing CSV
            path_avg_speed = self.config["static"] / "output_graph" / "avg_speed.csv"
            if path_avg_speed.is_file():
                avg_speeds = pd.read_csv(path_avg_speed)
            else:
                avg_speeds = calc_avg_speed(
                    G,
                    "highway",
                    save_csv=True,
                    save_path=self.config["static"] / "output_graph" / "avg_speed.csv",
                )
            G = assign_avg_speed(G, avg_speeds, "highway")

            # make a time value of seconds, length of road streches is in meters
            for u, v, k, edata in G.edges.data(keys=True):
                hours = (edata["length"] / 1000) / edata["avgspeed"]
                G[u][v][k]["time"] = round(hours * 3600, 0)

            return G
        else:
            logging.info(
                "No attributes found in the graph to estimate average speed per network segment."
            )
            return G

    def create(self) -> dict:
        """Handler function with the logic to call the right functions to create a network.

        Returns:
            (dict): A dict of a network (GeoDataFrame) and 1 (base NetworkX graph) or 2 graphs (base NetworkX and OD graph)
        """
        # Save the 'base' network as gpickle and if the user requested, also as shapefile.
        to_save = (
            ["pickle"] if not self.config["network"]["save_shp"] else ["pickle", "shp"]
        )
        od_graph = None
        base_graph = None
        network_gdf = None

        # For all graph and networks - check if it exists, otherwise, make the graph and/or network.
        if self.files["base_graph"] is None and self.files["base_network"] is None:
            # Create the network from the network source
            if self.config["network"]["source"] == "shapefile":
                logging.info("Start creating a network from the submitted shapefile.")
                base_graph, network_gdf = self.network_shp()

            elif self.config["network"]["source"] == "OSM PBF":
                logging.info(
                    """The original OSM PBF import is no longer supported. 
                                Instead, the beta version of package TRAILS is used. 
                                First stable release of TRAILS is excepted in 2023."""
                )

                # base_graph, network_gdf = self.network_osm_pbf() #The old approach is depreciated
                base_graph, network_gdf = self.network_trails_import()

            elif self.config["network"]["source"] == "OSM download":
                logging.info("Start downloading a network from OSM.")
                base_graph, network_gdf = self.network_osm_download()

            elif self.config["network"]["source"] == "pickle":
                logging.info("Start importing a network from pickle")
                base_graph = GraphPickleReader().read(
                    self.config["static"] / "output_graph" / "base_graph.p"
                )
                network_gdf = gpd.read_feather(
                    self.config["static"] / "output_graph" / "base_network.feather"
                )

                # Assuming the same CRS for both the network and graph
                self.base_graph_crs = pyproj.CRS.from_user_input(network_gdf.crs)
                self.base_network_crs = pyproj.CRS.from_user_input(network_gdf.crs)

            if (
                self.config["network"]["source"] != "pickle"
                and self.config["network"]["source"] != "shapefile"
                and self.config["network"]["source"] != "OSM PBF"
            ):
                # Graph & Network from OSM download or OSM PBF
                # Check if all geometries between nodes are there, if not, add them as a straight line.
                base_graph = add_missing_geoms_graph(base_graph, geom_name="geometry")
                base_graph = self.get_avg_speed(base_graph)

            # Save the graph and geodataframe
            self.files["base_graph"] = save_network(
                base_graph,
                self.config["static"] / "output_graph",
                "base_graph",
                types=to_save,
            )
            self.files["base_network"] = save_network(
                network_gdf,
                self.config["static"] / "output_graph",
                "base_network",
                types=to_save,
            )
        else:

            logging.info(
                "Apparently, you already did create a network with ra2ce earlier. "
                + "Ra2ce will use this: {}".format(self.files["base_graph"])
            )

            if self.files["base_graph"] is not None:
                base_graph = GraphPickleReader().read(self.files["base_graph"])
            else:
                base_graph = None

            if self.files["base_network"] is not None:
                network_gdf = gpd.read_feather(self.files["base_network"])
            else:
                network_gdf = None

            # Assuming the same CRS for both the network and graph
            self.base_graph_crs = pyproj.CRS.from_user_input(network_gdf.crs)
            self.base_network_crs = pyproj.CRS.from_user_input(network_gdf.crs)

        # create origins destinations graph
        if (
            (self.origins is not None)
            and (self.destinations is not None)
            and self.files["origins_destinations_graph"] is None
        ):
            # reading the base graphs
            if (self.files["base_graph"] is not None) and (base_graph is not None):
                base_graph = GraphPickleReader().read(self.files["base_graph"])
            # adding OD nodes
            if self.origins[0].suffix == ".tif":
                self.origins[0] = self.generate_origins_from_raster()
            od_graph = self.add_od_nodes(base_graph, self.base_graph_crs)
            self.files["origins_destinations_graph"] = save_network(
                od_graph,
                self.config["static"] / "output_graph",
                "origins_destinations_graph",
                types=to_save,
            )

        return {
            "base_graph": base_graph,
            "base_network": network_gdf,
            "origins_destinations_graph": od_graph,
        }
