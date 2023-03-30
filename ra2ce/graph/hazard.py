"""
GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2020 Deltares

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
import time
from typing import Any, List, Tuple, Union

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyproj
from osgeo import gdal
from rasterstats import point_query, zonal_stats

import ra2ce.graph.networks_utils as ntu
from ra2ce.io.readers import GraphPickleReader
from ra2ce.io.writers.network_exporter_factory import NetworkExporterFactory


class Hazard:
    """Class where the hazard overlay happens.

    Attributes:
        network: GeoDataFrame of the network.
        graphs: NetworkX graphs.
    """

    _ra2ce_name_key = "RA2CE name"

    def __init__(self, config: dict, graphs: dict, files: dict):
        self.config = config

        # graphs
        self.graphs = graphs

        # files
        self.files = files
        self.aggregate_wl = self.config["hazard"]["aggregate_wl"]
        self.hazard_files = {}  # Initiate the variable hazard_files
        self.get_hazard_files()

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

    def overlay_hazard_raster_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the hazard raster over the road segments GeoDataFrame.

        Args:
            *graph* (GeoDataFrame) : GeoDataFrame that will be intersected with the hazard map raster.

        Returns:

        """
        from tqdm import (
            tqdm,  # somehow this only works when importing here and not at the top of the file
        )

        assert type(gdf) == gpd.GeoDataFrame, "Network is not a GeoDataFrame"

        # Make sure none of the geometries is a nonetype object (this will raise an error in zonal_stats)
        empty_entries = gdf.loc[gdf.geometry.isnull()]
        if any(empty_entries):
            logging.warning(
                (
                    "Some geometries have NoneType objects (no coordinate information), namely: {}.".format(
                        empty_entries
                    )
                    + "This could be due to segmentation, and might cause an exception in hazard overlay"
                )
            )

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Validate input
            # Check if network and raster overlap
            extent_graph = gdf.total_bounds
            extent_graph = (
                extent_graph[0],
                extent_graph[2],
                extent_graph[1],
                extent_graph[3],
            )
            self._validate_extent_graph(extent_graph, i)

            tqdm.pandas(desc="Network hazard overlay with " + hn)
            _hazard_files_str = str(self.hazard_files["tif"][i])
            flood_stats = gdf.geometry.progress_apply(
                lambda x, _hz_str=_hazard_files_str: zonal_stats(
                    x,
                    _hz_str,
                    all_touched=True,
                    stats="min max",
                    add_stats={"mean": ntu.get_valid_mean},
                )
            )
            gdf[rn + "_mi"] = [x[0]["min"] for x in flood_stats]
            gdf[rn + "_ma"] = [x[0]["max"] for x in flood_stats]
            gdf[rn + "_me"] = [x[0]["mean"] for x in flood_stats]

            tqdm.pandas(desc="Network fraction with hazard overlay with " + hn)
            gdf[rn + "_fr"] = gdf.geometry.progress_apply(
                lambda x, _hz_str=_hazard_files_str: ntu.fraction_flooded(x, _hz_str)
            )
        return gdf

    def _get_edges_geoms(self, graph: nx.Graph) -> List[Any]:
        # Get all edge geometries
        return [
            (u, v, k, edata)
            for u, v, k, edata in graph.edges.data(keys=True)
            if "geometry" in edata
        ]

    def _validate_extent_graph(self, extent_graph, n_idx: int):
        # Check if the hazard and graph extents overlap
        extent = ntu.get_extent(gdal.Open(str(self.hazard_files["tif"][n_idx])))
        extent_hazard = (
            extent["minX"],
            extent["maxX"],
            extent["minY"],
            extent["maxY"],
        )

        if not ntu.bounds_intersect_2d(extent_graph, extent_hazard):
            logging.info(
                "Raster extent: {}, Graph extent: {}".format(extent, extent_graph)
            )
            raise ValueError(
                "The hazard raster and the graph geometries do not overlap, check projection"
            )

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
        from tqdm import tqdm

        # Verify the graph type (networkx)
        assert type(graph).__module__.split(".")[0] == "networkx"
        extent_graph = ntu.get_graph_edges_extent(graph)

        # Get all edge geometries
        edges_geoms = self._get_edges_geoms(graph)

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            self._validate_extent_graph(extent_graph, i)
            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(
                graph,
                {
                    (u, v, k): {rn + "_" + self.aggregate_wl[:2]: np.nan}
                    for u, v, k, edata in graph.edges.data(keys=True)
                    if "geometry" not in edata
                },
            )

            # Add the hazard values to the edges that do have a geometry
            gdf = gpd.GeoDataFrame(
                {"geometry": [edata["geometry"] for u, v, k, edata in edges_geoms]}
            )
            tqdm.pandas(desc="Graph hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files["tif"][i])
            if self.aggregate_wl == "mean":
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
                        stats=f"{self.aggregate_wl}",
                    )
                )

            try:
                flood_stats = flood_stats.apply(
                    lambda x: x[0][self.aggregate_wl] if x[0][self.aggregate_wl] else 0
                )
                nx.set_edge_attributes(
                    graph,
                    {
                        (edges[0], edges[1], edges[2]): {
                            rn + "_" + self.aggregate_wl[:2]: x
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

    def overlay_hazard_shp_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Overlays the hazard shapefile over the road segments GeoDataFrame.

        Args:
            gdf (GeoDataFrame): the network geodataframe that should be overlayed with the hazard shapefile(s)

        Returns:
            gdf (GeoDataFrame): the network geodataframe with hazard shapefile(s) data joined

        The gdf is reprojected to the hazard shapefile if necessary.
        """
        hfns = self.config["hazard"]["hazard_field_name"]
        gdf_crs_original = gdf.crs

        for i, (hn, rn, hfn) in enumerate(
            zip(self.hazard_names, self.ra2ce_names, hfns)
        ):
            gdf_hazard = gpd.read_file(str(self.hazard_files["shp"][i]))

            if gdf.crs != gdf_hazard.crs:
                gdf = gdf.to_crs(gdf_hazard.crs)

            gdf = gpd.sjoin(gdf, gdf_hazard[[hfn, "geometry"]], how="left")
            gdf.rename(columns={hfn: rn + "_" + self.aggregate_wl[:2]}, inplace=True)

        if gdf.crs != gdf_crs_original:
            gdf = gdf.to_crs(gdf_crs_original)

        return gdf

    def overlay_hazard_shp_graph(
        self, graph: nx.classes.graph.Graph
    ) -> nx.classes.graph.Graph:
        """Overlays the hazard shapefile over the road segments NetworkX graph.

        Args:
            graph (NetworkX graph): The graph that should be overlayed with the hazard shapefile(s)

        Returns:
            graph (NetworkX graph): The graph with hazard shapefile(s) data joined
        """
        # TODO check if the CRS of the graph and shapefile match

        hfns = self.config["hazard"]["hazard_field_name"]

        for i, (hn, rn, hfn) in enumerate(
            zip(self.hazard_names, self.ra2ce_names, hfns)
        ):
            gdf = gpd.read_file(str(self.hazard_files["shp"][i]))
            spatial_index = gdf.sindex

            for u, v, k, edata in graph.edges.data(keys=True):
                if "geometry" in edata:
                    possible_matches_index = list(
                        spatial_index.intersection(edata["geometry"].bounds)
                    )
                    possible_matches = gdf.iloc[possible_matches_index]
                    precise_matches = possible_matches[
                        possible_matches.intersects(edata["geometry"])
                    ]

                    if not precise_matches.empty:
                        if self.aggregate_wl == "max":
                            graph[u][v][k][
                                rn + "_" + self.aggregate_wl[:2]
                            ] = precise_matches[hfn].max()
                        if self.aggregate_wl == "min":
                            graph[u][v][k][
                                rn + "_" + self.aggregate_wl[:2]
                            ] = precise_matches[hfn].min()
                        if self.aggregate_wl == "mean":
                            graph[u][v][k][
                                rn + "_" + self.aggregate_wl[:2]
                            ] = np.nanmean(precise_matches[hfn])
                    else:
                        graph[u][v][k][rn + "_" + self.aggregate_wl[:2]] = 0
                else:
                    graph[u][v][k][rn + "_" + self.aggregate_wl[:2]] = 0

        return graph

    def od_hazard_intersect(
        self, graph: nx.classes.graph.Graph, ods: gpd.GeoDataFrame
    ) -> Tuple[nx.classes.graph.Graph, gpd.GeoDataFrame]:
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
        assert type(graph).__module__.split(".")[0] == "networkx"
        extent_graph = ntu.get_graph_edges_extent(graph)

        # Get all node geometries
        od_nodes = [(n, ndata) for n, ndata in graph.nodes.data() if "od_id" in ndata]
        od_ids = [n[0] for n in od_nodes]

        # Get all edge geometries
        edges_geoms = self._get_edges_geoms(graph)

        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Check if the hazard and graph extents overlap
            self._validate_extent_graph(extent_graph, i)

            # Read the hazard values at the nodes and write to the nodes.
            tqdm.pandas(desc="Destinations hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files["tif"][i])
            flood_stats = ods.geometry.progress_apply(
                lambda x, _file_values=_tif_hazard_files: point_query(x, _file_values)
            )

            flood_stats = flood_stats.apply(lambda x: x[0] if x[0] else 0)

            # Update the ODs GeoDataFrame
            ods[rn + "_" + self.aggregate_wl[:2]] = flood_stats

            # Update the graph
            attribute_dict = {
                od: {rn + "_" + self.aggregate_wl[:2]: wl}
                for od, wl in zip(od_ids, flood_stats)
            }
            nx.set_node_attributes(graph, attribute_dict)

            # Read the hazard values at the edges and write to the edges.
            # Add a no-data value for the edges that do not have a geometry
            nx.set_edge_attributes(
                graph,
                {
                    (u, v, k): {rn + "_" + self.aggregate_wl[:2]: np.nan}
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
                    stats=f"{self.aggregate_wl}",  # TODO: ADD MEAN WITHOUT THE NANs
                )
            )

            try:
                flood_stats = flood_stats.fillna(0)
                nx.set_edge_attributes(
                    graph,
                    {
                        (edges[0], edges[1], edges[2]): {
                            rn + "_" + self.aggregate_wl[:2]: x[0][self.aggregate_wl]
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
        from tqdm import tqdm

        ## Intersect the origin and destination nodes with the hazard map (now only geotiff possible)
        for i, (hn, rn) in enumerate(zip(self.hazard_names, self.ra2ce_names)):
            # Read the hazard values at the nodes and write to the nodes.
            tqdm.pandas(desc="Potentially isolated locations hazard overlay with " + hn)
            _tif_hazard_files = str(self.hazard_files["tif"][i])
            flood_stats = gdf.geometry.progress_apply(
                lambda x, _file_values=_tif_hazard_files: point_query(x, _file_values)
            )
            gdf[rn + "_" + self.aggregate_wl[:2]] = flood_stats.apply(
                lambda x: x[0] if x[0] else 0
            )

        return gdf

    def join_hazard_table_gdf(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs.

        Args:

        Returns:

        """
        for haz in self.hazard_files["table"]:
            if haz.suffix in [".csv"]:
                gdf = self.join_table(gdf, haz)
        return gdf

    def join_hazard_table_graph(
        self, graph: nx.classes.graph.Graph
    ) -> nx.classes.graph.Graph:
        """Joins a table with IDs and hazard information with the road segments with corresponding IDs.

        Args:

        Returns:

        """
        gdf, gdf_nodes = ntu.graph_to_gdf(graph, save_nodes=True)
        gdf = self.join_hazard_table_gdf(gdf)

        # TODO: Check if the graph is created again correctly.
        graph = ntu.graph_from_gdf(gdf, gdf_nodes)
        return graph

    def join_table(
        self, graph: nx.classes.graph.Graph, hazard: str
    ) -> nx.classes.graph.Graph:
        df = pd.read_csv(hazard)
        df = df[self.config["hazard"]["hazard_field_name"]]
        graph = graph.merge(
            df,
            how="left",
            left_on=self.config["network"]["file_id"],
            right_on=self.config["hazard"]["hazard_id"],
        )

        graph.rename(
            columns={
                self.config["hazard"]["hazard_field_name"]: [
                    n[:-3] for n in self.hazard_name_table[self._ra2ce_name_key]
                ][0]
            },
            inplace=True,
        )  # Check if this is the right name
        return graph

    def get_hazard_name_table(self) -> pd.DataFrame:
        all_agg_types = {
            "max": "maximum",
            "min": "minimum",
            "mean": "average",
            "fr": "fraction of network segment impacted by hazard",
        }
        chosen_agg_types = [all_agg_types[self.aggregate_wl], all_agg_types["fr"]]
        _hazard_map_config = self.config["hazard"]["hazard_map"]
        df = pd.DataFrame()
        df[["File name", "Aggregation method"]] = [
            (haz.stem, agg_type)
            for haz in _hazard_map_config
            for agg_type in chosen_agg_types
        ]
        if all(["RP" in haz.stem for haz in _hazard_map_config]):
            # Return period hazard maps are used
            # Note: no hazard type is indicated because the name became too long
            rps = [
                haz.stem.split("RP_")[-1].split("_")[0] for haz in _hazard_map_config
            ]
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
                for i in range(len(_hazard_map_config))
                for agg_type in chosen_agg_types
            ]
        df["Full path"] = [haz for haz in _hazard_map_config for _ in chosen_agg_types]
        return df

    def get_hazard_files(self):
        """Sorts the hazard files into tif, shp, and csv/json

        This function returns nothing but creates a dict self.hazard_files of hazard files sorted per type.
        {key = hazard file type (tif / shp / table (csv/json) : value = list of file paths}
        """
        _hazard_maps = self.config["hazard"]["hazard_map"]
        hazards_tif = [haz for haz in _hazard_maps if haz.suffix == ".tif"]
        hazards_shp = [haz for haz in _hazard_maps if haz.suffix == ".shp"]
        hazards_table = [haz for haz in _hazard_maps if haz.suffix in [".csv", ".json"]]

        self.hazard_files["tif"] = hazards_tif
        self.hazard_files["shp"] = hazards_shp
        self.hazard_files["table"] = hazards_table

    def get_hazard_intersect_geodataframe_tif(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
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

    def get_hazard_intersect_networkx_tif(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.overlay_hazard_raster_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_geodataframe_shp(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_gdf(to_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_networkx_shp(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_geodataframe_table(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.join_hazard_table_gdf(to_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_networkx_table(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.join_hazard_table_graph(to_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def hazard_intersect(
        self, to_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ) -> Union[gpd.GeoDataFrame, nx.classes.graph.Graph]:
        """Handler function that chooses the right function for overlaying the network with the hazard data."""
        if (self.hazard_files["tif"]) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_tif(to_overlay)
        elif (self.hazard_files["tif"]) and (
            type(to_overlay).__module__.split(".")[0] == "networkx"
        ):
            to_overlay = self.get_hazard_intersect_networkx_tif(to_overlay)
        elif (self.hazard_files["shp"]) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_shp(to_overlay)
        elif (self.hazard_files["shp"]) and (
            type(to_overlay).__module__.split(".")[0] == "networkx"
        ):
            to_overlay = self.get_hazard_intersect_networkx_shp(to_overlay)
        elif (self.hazard_files["table"]) and (type(to_overlay) == gpd.GeoDataFrame):
            to_overlay = self.get_hazard_intersect_geodataframe_table(to_overlay)
        elif (self.hazard_files["table"]) and (
            type(to_overlay).__module__.split(".")[0] == "networkx"
        ):
            to_overlay = self.get_hazard_intersect_networkx_table(to_overlay)
        else:
            logging.warning(
                f"The overlay of the combination of hazard file(s) '{self.hazard_files}' and network type '{type(to_overlay)}' is not available."
                f"Please check your input data."
            )

        return to_overlay

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

    def _export_network_files(self, graph_name: str, types_to_export: List[str]):
        _exporter = NetworkExporterFactory()
        _exporter.export(
            network=self.graphs[graph_name],
            basename=graph_name,
            output_dir=self.config["static"] / "output_graph",
            export_types=types_to_export,
        )
        self.files[graph_name] = _exporter.get_pickle_path()

    def load_origins_destinations(self):
        od_path = (
            self.config["static"] / "output_graph" / "origin_destination_table.feather"
        )
        od = gpd.read_feather(od_path)
        return od

    def create(self):
        """Overlays the different possible graph and network objects with the hazard data

        Arguments:
            None
            (implicit) : (self.graphs) : dictionary with the graph names as keys, and values the graphs
                        keys: ['base_graph', 'base_network', 'origins_destinations_graph']

        Returns:
            self.graph : same dictionary, but with new keys _hazard, which are copies of the graphs but with hazard data

        Effect:
            write all the objects

        """
        types_to_export = (
            ["pickle"] if not self.config["network"]["save_shp"] else ["pickle", "shp"]
        )

        if (
            self.files["base_graph"] is None
            and self.files["origins_destinations_graph"] is None
        ):
            logging.warning(
                "Either a base graph or OD graph is missing to intersect the hazard with. "
                "Check your network folder."
            )

        # Iterate over the three graph/network types to load the file if necessary (when not yet loaded in memory).
        for input_graph in ["base_graph", "base_network", "origins_destinations_graph"]:
            file_path = self.files[input_graph]

            if file_path is not None or self.graphs[input_graph] is not None:
                if self.graphs[input_graph] is None and input_graph != "base_network":
                    self.graphs[input_graph] = GraphPickleReader().read(file_path)
                elif self.graphs[input_graph] is None and input_graph == "base_network":
                    self.graphs[input_graph] = gpd.read_feather(file_path)

        #### Step 1: hazard overlay of the base graph (NetworkX) ###
        if self.files["base_graph"]:
            if self.files["base_graph_hazard"] is None:
                graph = self.graphs["base_graph"]

                # Check if the graph needs to be reprojected
                hazard_crs = pyproj.CRS.from_user_input(
                    self.config["hazard"]["hazard_crs"]
                )
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
                    graph_reprojected = self.get_reproject_graph(
                        graph, graph_crs, hazard_crs
                    )

                    # Do the actual hazard intersect
                    base_graph_hazard_reprojected = self.hazard_intersect(
                        graph_reprojected
                    )

                    # Assign the original geometries to the reprojected raster
                    self.graphs["base_graph_hazard"] = self.get_original_geoms_graph(
                        graph, base_graph_hazard_reprojected
                    )

                    # Clean up memory
                    ntu.clean_memory([graph_reprojected, base_graph_hazard_reprojected])
                else:
                    self.graphs["base_graph_hazard"] = self.hazard_intersect(graph)

                # Save graphs/network with hazard
                self._export_network_files("base_graph_hazard", types_to_export)
            else:
                try:
                    # Try to find the base graph hazard file
                    self.graphs["base_graph_hazard"] = GraphPickleReader().read(
                        self.config["static"] / "output_graph" / "base_graph_hazard.p"
                    )
                except FileNotFoundError:
                    # File not found
                    logging.warning(
                        f"Base graph hazard file not found at {self.config['static'] / 'output_graph' / 'base_graph_hazard.p'}"
                    )

        #### Step 2: hazard overlay of the origins_destinations (NetworkX) ###
        if (
            self.files["origins_destinations_graph"]
            and (self.config["origins_destinations"]["origins"])
            and (self.config["origins_destinations"]["destinations"])
            and (self.files["origins_destinations_graph_hazard"] is None)
        ):
            graph = self.graphs["origins_destinations_graph"]
            ods = self.load_origins_destinations()

            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self.config["hazard"]["hazard_crs"])
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
                self.graphs[
                    "origins_destinations_graph_hazard"
                ] = self.get_original_geoms_graph(graph, od_graph_hazard_reprojected)
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
                    self.graphs["origins_destinations_graph_hazard"],
                    ods,
                ) = self.od_hazard_intersect(graph, ods)

            # Save graphs/network with hazard
            self._export_network_files(
                "origins_destinations_graph_hazard", types_to_export
            )

            # Save the OD pairs (GeoDataFrame) as pickle
            ods.to_feather(
                self.config["static"]
                / "output_graph"
                / "origin_destination_table.feather",
                index=False,
            )
            logging.info(
                f"Saved {'origin_destination_table.feather'} in {self.config['static'] / 'output_graph'}."
            )

            # Save the OD pairs (GeoDataFrame) as shapefile
            if self.config["network"]["save_shp"]:
                ods_path = (
                    self.config["static"]
                    / "output_graph"
                    / "origin_destination_table.shp"
                )
                ods.to_file(ods_path, index=False)
                logging.info(f"Saved {ods_path.stem} in {ods_path.resolve().parent}.")

        #### Step 3: iterate overlay of the GeoPandas Dataframe (if any) ###
        if self.files["base_network"] and self.files["base_network_hazard"] is None:
            # Check if the graph needs to be reprojected
            hazard_crs = pyproj.CRS.from_user_input(self.config["hazard"]["hazard_crs"])
            gdf_crs = pyproj.CRS.from_user_input(self.graphs["base_network"].crs)

            if (
                hazard_crs != gdf_crs
            ):  # Temporarily reproject the graph to the CRS of the hazard
                logging.warning(
                    """Hazard crs {} and gdf crs {} are inconsistent,
                                                we try to reproject the gdf crs""".format(
                        hazard_crs, gdf_crs
                    )
                )
                extent_gdf = self.graphs["base_network"].total_bounds
                logging.info("Gdf extent before reprojecting: {}".format(extent_gdf))
                gdf_reprojected = self.graphs["base_network"].copy().to_crs(hazard_crs)
                extent_gdf_reprojected = gdf_reprojected.total_bounds
                logging.info(
                    "Gdf extent after reprojecting: {}".format(extent_gdf_reprojected)
                )

                # Do the actual hazard intersect
                gdf_reprojected = self.hazard_intersect(gdf_reprojected)

                # Assign the original geometries to the reprojected raster
                original_geometries = self.graphs["base_network"]["geometry"]
                gdf_reprojected["geometry"] = original_geometries
                self.graphs["base_network_hazard"] = gdf_reprojected.copy()
                del gdf_reprojected
            else:
                self.graphs["base_network_hazard"] = self.hazard_intersect(
                    self.graphs["base_network"]
                )

            # Save graphs/network with hazard
            self._export_network_files("base_network_hazard", types_to_export)

        #### Step 4: hazard overlay of the locations that are checked for isolation ###
        if "isolation" in self.config and self.config["isolation"]["locations"]:
            locations = gpd.read_file(self.config["isolation"]["locations"][0])
            locations["i_id"] = locations.index
            locations_crs = pyproj.CRS.from_user_input(locations.crs)
            hazard_crs = pyproj.CRS.from_user_input(self.config["hazard"]["hazard_crs"])

            if (
                hazard_crs != locations_crs
            ):  # Temporarily reproject the locations to the CRS of the hazard
                logging.warning(
                    """Hazard crs {} and location crs {} are inconsistent,
                                                we try to reproject the location crs""".format(
                        hazard_crs, locations_crs
                    )
                )
                extent_locations = locations.total_bounds
                logging.info(
                    "Gdf extent before reprojecting: {}".format(extent_locations)
                )
                locations_reprojected = locations.copy().to_crs(hazard_crs)
                extent_locations_reprojected = locations_reprojected.total_bounds
                logging.info(
                    "Gdf extent after reprojecting: {}".format(
                        extent_locations_reprojected
                    )
                )

                # Do the actual hazard intersect
                locations_reprojected = self.point_hazard_intersect(
                    locations_reprojected
                )

                # Assign the original geometries to the reprojected raster
                original_geometries = locations["geometry"]
                locations_reprojected["geometry"] = original_geometries
                locations = locations_reprojected.copy()
                del locations_reprojected
            else:
                locations = self.point_hazard_intersect(locations)

            _exporter = NetworkExporterFactory()
            _exporter.export(
                network=locations,
                basename="locations_hazard",
                output_dir=self.config["static"] / "output_graph",
                export_types=["pickle"],
            )

        # Save the hazard name bookkeeping table.
        self.hazard_name_table.to_excel(
            self.config["output"] / "hazard_names.xlsx", index=False
        )

        return self.graphs
