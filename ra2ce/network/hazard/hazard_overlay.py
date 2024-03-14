"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyproj
from rasterstats import point_query, zonal_stats
from tqdm import tqdm

from ra2ce.network import networks_utils as ntu
from ra2ce.network.exporters.network_exporter_factory import NetworkExporterFactory
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.hazard.hazard_common_functions import (
    get_edges_geoms,
    validate_extent_graph,
)
from ra2ce.network.hazard.hazard_files import HazardFiles
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_for_gpkg import (
    HazardIntersectBuilderForGpkg,
)
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_for_table import (
    HazardIntersectBuilderForTable,
)
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_for_tif import (
    HazardIntersectBuilderForTif,
)
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData


class HazardOverlay:
    """Class where the hazard overlay happens.

    Attributes:
        network: GeoDataFrame of the network.
        graph_files: NetworkX graphs.
    """

    _ra2ce_name_key = "RA2CE name"

    def __init__(
        self,
        config: NetworkConfigData,
        graph_files: GraphFilesCollection,
    ):
        # Sections properties
        self._network_file_id = config.network.file_id
        self._output_graph_dir = config.static_path.joinpath("output_graph")
        self._output_dir = config.output_path
        self._origins = config.origins_destinations.origins
        self._destinations = config.origins_destinations.destinations
        self._save_gpkg = config.network.save_gpkg
        self._isolation_locations = config.static_path.joinpath(
            "network", config.isolation.locations
        )
        if config.static_path.joinpath("network", config.isolation.locations).is_file():
            self._isolation_locations = config.static_path.joinpath(
                "network", config.isolation.locations
            )
        else:
            self._isolation_locations = None
        # Hazard properties
        self._hazard_field_name = config.hazard.hazard_field_name
        self._hazard_id = config.hazard.hazard_id
        self._hazard_map = config.hazard.hazard_map
        self._hazard_crs = config.hazard.hazard_crs
        self._hazard_aggregate_wl = config.hazard.aggregate_wl.config_value
        self._hazard_directory = config.static_path.joinpath("hazard")

        # graph files
        self.graph_files = graph_files

        # files
        self.hazard_files = HazardFiles.from_hazard_map(self._hazard_map)

        # bookkeeping for the hazard map names
        self.hazard_name_table = self.get_hazard_name_table()
        self.hazard_names = list(
            dict.fromkeys(list(self.hazard_name_table["File name"]))
        )
        self.ra2ce_names = list(
            dict.fromkeys(
                [n[:-3] for n in self.hazard_name_table[self._ra2ce_name_key]]
            )
        )
        logging.info("Initialized hazard object.")

    def overlay_hazard_raster_graph(
        self, graph: nx.classes.graph.Graph
    ) -> nx.classes.graph.Graph:
        """Overlays the hazard raster over the road segments graph.

        Args:
            *hf* (list of Pathlib paths) : #not sure if this is needed as argument if we also read if from the config
            *graph* (NetworkX Graph) : NetworkX graph with geometries that will be intersected with the hazard map raster.

        Returns:
            *graph* (NetworkX Graph) : NetworkX graph with hazard values
        """

        # Verify the graph type (networkx)
        assert isinstance(graph, nx.classes.graph.Graph)
        extent_graph = ntu.get_graph_edges_extent(graph)

        # Get all edge geometries
        edges_geoms = get_edges_geoms(graph)

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            validate_extent_graph(extent_graph, self.hazard_files.tif[i])
            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(
                graph,
                {
                    (u, v, k): {rn + "_" + self._hazard_aggregate_wl[:2]: np.nan}
                    for u, v, k, edata in graph.edges.data(keys=True)
                    if "geometry" not in edata
                },
            )

            # Add the hazard values to the edges that do have a geometry
            gdf = gpd.GeoDataFrame(
                {"geometry": [edata["geometry"] for u, v, k, edata in edges_geoms]}
            )
            tqdm.pandas(desc="Graph hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files.tif[i])
            if self._hazard_aggregate_wl == "mean":
                flood_stats = gdf.geometry.progress_apply(
                    lambda x, _files_value=_tif_hazard_files: zonal_stats(
                        x,
                        _files_value,
                        all_touched=True,
                        add_stats={"mean": ntu.get_valid_mean},
                    )
                )
            else:
                flood_stats = gdf.geometry.progress_apply(
                    lambda x, _files_value=_tif_hazard_files: zonal_stats(
                        x,
                        _files_value,
                        all_touched=True,
                        stats=f"{self._hazard_aggregate_wl}",
                    )
                )

            try:
                flood_stats = flood_stats.apply(
                    lambda x: (
                        x[0][self._hazard_aggregate_wl]
                        if x[0][self._hazard_aggregate_wl]
                        else 0
                    )
                )
                nx.set_edge_attributes(
                    graph,
                    {
                        (edges[0], edges[1], edges[2]): {
                            rn + "_" + self._hazard_aggregate_wl[:2]: x
                        }
                        for x, edges in zip(flood_stats, edges_geoms)
                    },
                )
            except KeyError:
                logging.warning(
                    "No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'."
                )

            # Get the fraction of the road that is intersecting with the hazard
            tqdm.pandas(desc="Graph fraction with hazard overlay with " + hn)
            graph_fraction_flooded = gdf.geometry.progress_apply(
                lambda x, _files_values=_tif_hazard_files: ntu.fraction_flooded(
                    x, _files_values
                )
            )
            graph_fraction_flooded = graph_fraction_flooded.fillna(0)
            nx.set_edge_attributes(
                graph,
                {
                    (edges[0], edges[1], edges[2]): {rn + "_fr": x}
                    for x, edges in zip(graph_fraction_flooded, edges_geoms)
                },
            )

        return graph

    def od_hazard_intersect(
        self, graph: nx.classes.graph.Graph, ods: gpd.GeoDataFrame
    ) -> tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
        """Overlays the origin and destination locations and edges with the hazard maps

        Args:
            graph (NetworkX graph): The origin-destination graph that should be overlayed with the hazard raster(s)

        Returns:
            graph (NetworkX graph): The origin-destination graph hazard raster(s) data joined to both the origin- and
            destination nodes and the edges.
        """
        ## Intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        # Verify the graph type (networkx)
        assert isinstance(graph, nx.classes.graph.Graph)
        extent_graph = ntu.get_graph_edges_extent(graph)

        # Get all node geometries
        od_nodes = [(n, ndata) for n, ndata in graph.nodes.data() if "od_id" in ndata]
        od_ids = [n[0] for n in od_nodes]

        # Get all edge geometries
        edges_geoms = get_edges_geoms(graph)

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            validate_extent_graph(extent_graph, self.hazard_files.tif[i])

            # Read the hazard values at the nodes and write to the nodes.
            tqdm.pandas(desc="Destinations hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files.tif[i])
            flood_stats = ods.geometry.progress_apply(
                lambda x, _file_values=_tif_hazard_files: point_query(x, _file_values)
            )

            flood_stats = flood_stats.apply(lambda x: x[0] if x[0] else 0)

            # Update the ODs GeoDataFrame
            ods[rn + "_" + self._hazard_aggregate_wl[:2]] = flood_stats

            # Update the graph
            attribute_dict = {
                od: {rn + "_" + self._hazard_aggregate_wl[:2]: wl}
                for od, wl in zip(od_ids, flood_stats)
            }
            nx.set_node_attributes(graph, attribute_dict)

            # Read the hazard values at the edges and write to the edges.
            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(
                graph,
                {
                    (u, v, k): {rn + "_" + self._hazard_aggregate_wl[:2]: np.nan}
                    for u, v, k, edata in graph.edges.data(keys=True)
                    if "geometry" not in edata
                },
            )

            # Add the hazard values to the edges that do have a geometry
            gdf = gpd.GeoDataFrame(
                {"geometry": [edata["geometry"] for u, v, k, edata in edges_geoms]}
            )
            tqdm.pandas(desc="OD graph hazard overlay with " + hn)
            flood_stats = gdf.geometry.progress_apply(
                lambda x, _files_values=_tif_hazard_files: zonal_stats(
                    x,
                    _files_values,
                    all_touched=True,
                    stats=f"{self._hazard_aggregate_wl}",  # TODO: ADD MEAN WITHOUT THE NANs
                )
            )

            try:
                flood_stats = flood_stats.fillna(0)
                nx.set_edge_attributes(
                    graph,
                    {
                        (edges[0], edges[1], edges[2]): {
                            rn
                            + "_"
                            + self._hazard_aggregate_wl[:2]: x[0][
                                self._hazard_aggregate_wl
                            ]
                        }
                        for x, edges in zip(flood_stats, edges_geoms)
                    },
                )
            except Exception:
                logging.warning(
                    "No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'."
                )

            # Get the fraction of the road that is intersecting with the hazard
            tqdm.pandas(desc="OD graph fraction with hazard overlay with " + hn)
            graph_fraction_flooded = gdf.geometry.progress_apply(
                lambda x, _files_values=_tif_hazard_files: ntu.fraction_flooded(
                    x, _files_values
                )
            )
            graph_fraction_flooded = graph_fraction_flooded.fillna(0)
            nx.set_edge_attributes(
                graph,
                {
                    (edges[0], edges[1], edges[2]): {rn + "_fr": x}
                    for x, edges in zip(graph_fraction_flooded, edges_geoms)
                },
            )

        return graph, ods

    def point_hazard_intersect(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the point locations with hazard maps

        Args:
            gdf (GeoDataFrame): the point geodataframe that should be overlayed with the hazard raster(s)
        Returns:
            gdf (GeoDataFrame): the point geodataframe with hazard raster(s) data joined
        """

        ## Intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Read the hazard values at the nodes and write to the nodes.
            tqdm.pandas(desc="Potentially isolated locations hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files.tif[i])
            flood_stats = gdf.geometry.progress_apply(
                lambda x, _file_values=_tif_hazard_files: point_query(x, _file_values)
            )
            gdf[rn + "_" + self._hazard_aggregate_wl[:2]] = flood_stats.apply(
                lambda x: x[0] if x[0] else 0
            )

        return gdf

    def get_point_hazard_from_network(
        self, points: gpd.GeoDataFrame, network: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """get hazard informations for points at nearest network locations.

        Args:
            points (gpd.GeoDataFrame): points of interest, will be snapped to the network by nearest distance method.
            network (gpd.GeoDataFrame): network of interest

        Returns:
            gpd.GeoDataFrame: points with relation to network and hazard informations

        Raise:
            error: if node id columns do not exisit in the network
        """

        # TODO: use the same convention for shapefiles and osm
        if all(
            c_idx in network.columns for c_idx in ["node_A", "node_B"]
        ):  # shapefiles
            network["edge_fid"] = [
                f"{na}_{nb}" for na, nb in network[["node_A", "node_B"]].values
            ]
        elif all(c_idx in network.columns for c_idx in ["u", "v"]):  # osm
            network["edge_fid"] = [
                f"{na}_{nb}" for na, nb in network[["u", "v"]].values
            ]
        else:
            logging.error(
                "Node id columns are not found in the network. Support node_A, node_B or u, v"
            )

        # check for crs
        if points.crs.is_geographic:
            crs = points.crs
            points = points.to_crs(3857)
            network = network.to_crs(points.crs)

        points = gpd.sjoin_nearest(
            points, network, how="left", distance_col="edges_distance"
        )
        if any(points["edges_distance"].isna()) > 0:
            logging.warning("Not all points are snapped to the network.")

        return points.to_crs(crs)

    def get_hazard_name_table(self) -> pd.DataFrame:
        all_agg_types = {
            "max": "maximum",
            "min": "minimum",
            "mean": "average",
            "fr": "fraction of network segment impacted by hazard",
        }
        chosen_agg_types = [
            all_agg_types[self._hazard_aggregate_wl],
            all_agg_types["fr"],
        ]
        df = pd.DataFrame()
        df[["File name", "Aggregation method"]] = [
            (haz.stem, agg_type)
            for haz in self._hazard_map
            for agg_type in chosen_agg_types
        ]
        if all(["RP" in haz.stem for haz in self._hazard_map]):
            # Return period hazard maps are used
            # Note: no hazard type is indicated because the name became too long
            rps = [haz.stem.split("RP_")[-1].split("_")[0] for haz in self._hazard_map]
            df[self._ra2ce_name_key] = [
                "RP" + rp + "_" + agg_type[:2]
                for rp in rps
                for agg_type in chosen_agg_types
            ]
        else:
            # Event hazard maps are used
            # Note: no hazard type is indicated because the name became too long
            df[self._ra2ce_name_key] = [
                "EV" + str(i + 1) + "_" + agg_type[:2]
                for i in range(len(self._hazard_map))
                for agg_type in chosen_agg_types
            ]
        df["Full path"] = [haz for haz in self._hazard_map for _ in chosen_agg_types]
        return df

    def hazard_intersect(
        self, to_overlay: gpd.GeoDataFrame | nx.classes.graph.Graph
    ) -> gpd.GeoDataFrame | nx.classes.graph.Graph:
        """Handler function that chooses the right function for overlaying the network with the hazard data."""
        # To improve performance we need to initialize the variables
        if self.hazard_files.tif:
            return HazardIntersectBuilderForTif(
                hazard_aggregate_wl=self._hazard_aggregate_wl,
                hazard_names=self.hazard_names,
                ra2ce_names=self.ra2ce_names,
                hazard_tif_files=self.hazard_files.tif,
            ).get_intersection(to_overlay)
        elif self.hazard_files.gpkg:
            return HazardIntersectBuilderForGpkg(
                hazard_field_name=self._hazard_field_name,
                hazard_aggregate_wl=self._hazard_aggregate_wl,
                hazard_names=self.hazard_names,
                ra2ce_names=self.ra2ce_names,
                hazard_gpkg_files=self.hazard_files.gpkg,
            ).get_intersection(to_overlay)
        elif self.hazard["table"]:
            return HazardIntersectBuilderForTable(
                hazard_field_name=self._hazard_field_name,
                network_file_id=self._network_file_id,
                hazard_id=self._hazard_id,
                ra2ce_name_key=self._ra2ce_name_key,
            ).get_intersection(to_overlay)

        raise ValueError(
            f"The overlay of the combination of hazard file(s) '{self.hazard_files}' and network type '{type(to_overlay)}' is not available."
            f"Please check your input data."
        )

    def get_reproject_graph(
        self,
        original_graph: nx.classes.graph.Graph,
        in_crs: pyproj.CRS,
        out_crs: pyproj.CRS,
    ) -> nx.classes.graph.Graph:
        """Reproject networkX graph"""
        extent_graph = ntu.get_graph_edges_extent(original_graph)
        logging.info("Graph extent before reprojecting: {}".format(extent_graph))
        graph_reprojected = ntu.reproject_graph(original_graph, in_crs, out_crs)
        extent_graph_reprojected = ntu.get_graph_edges_extent(graph_reprojected)
        logging.info(
            "Graph extent after reprojecting: {}".format(extent_graph_reprojected)
        )
        return graph_reprojected

    def get_original_geoms_graph(self, graph_original, graph_new):
        original_geometries = nx.get_edge_attributes(graph_original, "geometry")
        _graph_new = graph_new.copy()
        nx.set_edge_attributes(_graph_new, original_geometries, "geometry")
        return _graph_new.copy()

    def _export_network_files(self, graph_type: str, types_to_export: list[str]):
        _exporter = NetworkExporterFactory()
        _exporter.export(
            network=self.graph_files.get_graph(graph_type),
            basename=graph_type,
            output_dir=self._output_graph_dir,
            export_types=types_to_export,
        )
        self.graph_files.set_file(_exporter.get_pickle_path())

    def load_origins_destinations(self):
        od_path = self._output_graph_dir.joinpath("origin_destination_table.feather")
        od = gpd.read_feather(od_path)
        return od

    def hazard_intersect_with_reprojection(
        self, gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Intersect geodataframe and hazard with reprojection"""
        # Check if the graph needs to be reprojected
        hazard_crs = pyproj.CRS.from_user_input(self.config.hazard["hazard_crs"])
        gdf_crs = pyproj.CRS.from_user_input(gdf.crs)

        if (
            hazard_crs != gdf_crs
        ):  # Temporarily reproject the graph to the CRS of the hazard
            logging.warning(
                """Hazard crs {} and gdf crs {} are inconsistent,
                                            we try to reproject the gdf crs""".format(
                    hazard_crs, gdf_crs
                )
            )
            extent_gdf = gdf.total_bounds
            logging.info("Gdf extent before reprojecting: {}".format(extent_gdf))
            gdf_reprojected = gdf.to_crs(hazard_crs)
            extent_gdf_reprojected = gdf_reprojected.total_bounds
            logging.info(
                "Gdf extent after reprojecting: {}".format(extent_gdf_reprojected)
            )

            # Do the actual hazard intersect
            gdf_reprojected = self.hazard_intersect(gdf_reprojected)

            # reassign crs
            gdf_output = gdf_reprojected.to_crs(gdf_crs)

        else:
            gdf_output = self.hazard_intersect(gdf)

        return gdf_output

    def create(self):
        """Overlays the different possible graph and network objects with the hazard data

        Arguments:
            None
            (implicit) : (self.graphs_files) : GraphFile object with the graph names and files as attributes

        Returns:
            self.graph_files : same object, but with new graphs _hazard, which are copies of the graphs but with hazard data

        Effect:
            write all the objects

        """
        types_to_export = ["pickle"] if not self._save_gpkg else ["pickle", "gpkg"]

        if (
            not self.graph_files.base_graph.file
            and not self.graph_files.origins_destinations_graph.file
        ):
            logging.warning(
                "Either a base graph or OD graph is missing to intersect the hazard with. "
                "Check your network folder."
            )

        #### Step 1: hazard overlay of the base graph (NetworkX) ###
        if self.graph_files.base_graph.file:
            if self.graph_files.base_graph_hazard.file is None:
                graph = self.graph_files.base_graph.get_graph()

                # Check if the graph needs to be reprojected
                hazard_crs = pyproj.CRS.from_user_input(self._hazard_crs)
                graph_crs = pyproj.CRS.from_user_input(
                    "EPSG:4326"
                )  # this is WGS84, TODO: Make flexible by including in the network ini

                if hazard_crs != graph_crs:
                    # Temporarily reproject the graph to the CRS of the hazard
                    logging.warning(
                        """Hazard crs {} and graph crs {} are inconsistent,
                                                  we try to reproject the graph crs""".format(
                            hazard_crs, graph_crs
                        )
                    )
                    graph_reprojected = self.get_reproject_graph(
                        graph, graph_crs, hazard_crs
                    )

                    # Do the actual hazard intersect
                    base_graph_hazard_reprojected = self.hazard_intersect(
                        graph_reprojected
                    )

                    # Assign the original geometries to the reprojected raster
                    self.graph_files.base_graph_hazard.graph = (
                        self.get_original_geoms_graph(
                            graph, base_graph_hazard_reprojected
                        )
                    )

                    # Clean up memory
                    ntu.clean_memory([graph_reprojected, base_graph_hazard_reprojected])
                else:
                    self.graph_files.base_graph_hazard.graph = self.hazard_intersect(
                        graph
                    )

                # Save graphs/network with hazard
                self._export_network_files("base_graph_hazard", types_to_export)

        #### Step 2: hazard overlay of the origins_destinations (NetworkX) ###
        if (
            self.graph_files.origins_destinations_graph.file
            and self._origins
            and self._destinations
            and (not self.graph_files.origins_destinations_graph_hazard.file)
        ):
            graph = self.graph_files.origins_destinations_graph.get_graph()
            ods = self.load_origins_destinations()

            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self._hazard_crs)
            graph_crs = pyproj.CRS.from_user_input(
                "EPSG:4326"
            )  # this is WGS84, TODO: Make flexible by including in the network ini

            if (
                hazard_crs != graph_crs
            ):  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning(
                    """Hazard crs {} and graph crs {} are inconsistent,
                                                  we try to reproject the graph crs""".format(
                        hazard_crs, graph_crs
                    )
                )
                if hazard_crs != ods.crs:
                    logging.warning(
                        """Hazard crs {} and OD crs {} are inconsistent,
                                                      we try to reproject the graph crs""".format(
                            hazard_crs, ods.crs
                        )
                    )
                    ods_reprojected = ods.to_crs(hazard_crs)

                graph_reprojected = self.get_reproject_graph(
                    graph, graph_crs, hazard_crs
                )

                # Do the actual hazard intersect
                (
                    od_graph_hazard_reprojected,
                    ods_hazard_reprojected,
                ) = self.od_hazard_intersect(graph_reprojected, ods_reprojected)

                # Assign the original geometries to the reprojected dataset
                self.graph_files.origins_destinations_graph_hazard.graph = (
                    self.get_original_geoms_graph(graph, od_graph_hazard_reprojected)
                )
                ods = ods_hazard_reprojected.to_crs(ods.crs)

                # Clean up memory
                ntu.clean_memory(
                    [
                        graph_reprojected,
                        od_graph_hazard_reprojected,
                        ods_reprojected,
                        ods_hazard_reprojected,
                    ]
                )

            else:
                (
                    self.graph_files.origins_destinations_graph_hazard.graph,
                    ods,
                ) = self.od_hazard_intersect(graph, ods)

            # Save graphs/network with hazard
            self._export_network_files(
                "origins_destinations_graph_hazard", types_to_export
            )

            # Save the OD pairs (GeoDataFrame) as pickle
            _od_table_feather = self._output_graph_dir.joinpath(
                "origin_destination_table.feather"
            )
            ods.to_feather(
                _od_table_feather,
                index=False,
            )
            logging.info(
                f"Saved {_od_table_feather.name} in {_od_table_feather.parent}."
            )

            # Save the OD pairs (GeoDataFrame) as shapefile
            if self._save_gpkg:
                ods_path = self._output_graph_dir.joinpath(
                    "origin_destination_table.gpkg"
                )
                ods.to_file(ods_path, index=False)
                logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        #### Step 3: iterate overlay of the GeoPandas Dataframe (if any) ###
        if (
            self.graph_files.base_network.file
            and not self.graph_files.base_network_hazard.file
        ):
            logging.info("Iterating overlay of GeoPandas Dataframe.")
            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self._hazard_crs)
            gdf_crs = pyproj.CRS.from_user_input(
                self.graph_files.base_network.get_graph().crs
            )

            if (
                hazard_crs != gdf_crs
            ):  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning(
                    """Hazard crs {} and gdf crs {} are inconsistent,
                                                we try to reproject the gdf crs""".format(
                        hazard_crs, gdf_crs
                    )
                )
                extent_gdf = self.graph_files.base_network.get_graph().total_bounds
                logging.info("Gdf extent before reprojecting: {}".format(extent_gdf))
                gdf_reprojected = self.graph_files.base_network.graph.copy().to_crs(
                    hazard_crs
                )
                extent_gdf_reprojected = gdf_reprojected.total_bounds
                logging.info(
                    "Gdf extent after reprojecting: {}".format(extent_gdf_reprojected)
                )

                # Do the actual hazard intersect
                gdf_reprojected = self.hazard_intersect(gdf_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = self.graph_files.base_network.get_graph()[
                    "geometry"
                ]
                gdf_reprojected["geometry"] = original_geometries
                self.graph_files.base_network_hazard.graph = gdf_reprojected.copy()
                del gdf_reprojected
            else:
                # read previously created file
                logging.info("Setting 'base_network_hazard' graph.")
                if not self.graph_files.base_network_hazard.file:
                    self.graph_files.base_network_hazard.graph = self.hazard_intersect(
                        self.graph_files.base_network.get_graph()
                    )

        #### Step 4: hazard overlay of the locations that are checked for isolation ###
        if self._isolation_locations:
            logging.info("Detected isolated locations, checking for hazard overlay.")
            locations = gpd.read_file(self._isolation_locations, engine="pyogrio")
            locations["i_id"] = locations.index

            # get hazard at locations from network based on nearest
            logging.info("Get hazard at locations from network.")
            locations_hazard = self.get_point_hazard_from_network(
                locations, self.graph_files.base_network_hazard.get_graph()
            )

            _exporter = NetworkExporterFactory()
            _exporter.export(
                network=locations_hazard,
                basename="locations_hazard",
                output_dir=self._output_graph_dir,
                export_types=["pickle"],
            )

        # Save the hazard name bookkeeping table.
        self.hazard_name_table.to_excel(
            self._output_dir.joinpath("hazard_names.xlsx"), index=False
        )

        return self.graph_files
