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

import math
from pathlib import Path
from pyproj import CRS
import geopandas as gpd
import pandas as pd
import ra2ce.graph.networks_utils as nut
from shapely.geometry import MultiLineString
import logging
import networkx as nx

from ra2ce.graph.segmentation import Segmentation


class ShpNetworkWrapper:
    primary_files: list[Path]
    region_path: Path
    crs: CRS
    directed: bool
    file_id: str

    def __init__(
        self,
        primary_files: list[Path],
        diversion_files: list[Path],
        region_path: Path,
        crs_value: str,
        is_directed: bool,
        file_id: str,
    ) -> None:
        """Initializes the VectorNetworkWrapper object.

        Args:
            config (dict): Configuration dictionary.

        Raises:
            ValueError: If the config is None or doesn't contain a network dictionary,
                or if config['network'] is not a dictionary.
        """
        self.primary_files = primary_files
        self.diversion_files = diversion_files
        self.crs = CRS.from_user_input(crs_value if crs_value else "epsg:4326")
        self.region_path = region_path
        self.directed = is_directed
        self.file_id = file_id

    def read_merge_shp(self) -> gpd.GeoDataFrame:
        """Imports shapefile(s) and saves attributes in a pandas dataframe.

        Returns:
            lines (list of shapely LineStrings): full list of linestrings
            properties (pandas dataframe): attributes of shapefile(s), in order of the linestrings in lines
        """
        # concatenate all shapefile into one geodataframe and set analysis to 1 or 0 for diversions
        lines = [gpd.read_file(shp) for shp in self.primary_files]

        if any(self.diversion_files):
            lines.extend(
                [
                    nut.check_crs_gdf(gpd.read_file(shp), self.crs)
                    for shp in self.diversion_files
                ]
            )
        lines = pd.concat(lines)

        lines.crs = self.crs

        # Check if there are any multilinestrings and convert them to linestrings.
        if lines["geometry"].apply(lambda row: isinstance(row, MultiLineString)).any():
            mls_idx = lines.loc[
                lines["geometry"].apply(lambda row: isinstance(row, MultiLineString))
            ].index
            for idx in mls_idx:
                # Multilinestrings to linestrings
                new_rows_geoms = list(lines.iloc[idx]["geometry"].geoms)
                for nrg in new_rows_geoms:
                    dict_attributes = dict(lines.iloc[idx])
                    dict_attributes["geometry"] = nrg
                    lines.loc[max(lines.index) + 1] = dict_attributes

            lines = lines.drop(labels=mls_idx, axis=0)

        # append the length of the road stretches
        lines["length"] = lines["geometry"].apply(
            lambda x: nut.line_length(x, self.crs)
        )

        logging.info(
            "Shapefile(s) loaded with attributes: {}.".format(
                list(lines.columns.values)
            )
        )  # fill in parameter names

        return lines

    def _get_complex_graph_and_edges(
        self, edges: gpd.GeoDataFrame, id_name: str
    ) -> tuple[nx.MultiGraph, gpd.GeoDataFrame]:
        # Get the unique points at the end of lines and at intersections to create nodes
        nodes = nut.create_nodes(edges, self.crs, self._cleanup.cut_at_intersections)
        logging.info("Function [create_nodes]: executed")

        edges = nut.cut_lines(
            edges, nodes, id_name, tolerance=0.00001, crs_=self.crs
        )  ## PAY ATTENTION TO THE TOLERANCE, THE UNIT IS DEGREES
        logging.info("Function [cut_lines]: executed")

        if not edges.crs:
            edges.crs = self.crs

        # create tuples from the adjecent nodes and add as column in geodataframe
        edges_complex = nut.join_nodes_edges(nodes, edges, id_name)
        edges_complex.crs = self.crs  # set the right CRS
        edges_complex.dropna(subset=["node_A", "node_B"], inplace=True)

        assert (
            edges_complex["node_A"].isnull().sum() == 0
        ), "Some edges cannot be assigned nodes, please check your input shapefile."
        assert (
            edges_complex["node_B"].isnull().sum() == 0
        ), "Some edges cannot be assigned nodes, please check your input shapefile."

        # Create networkx graph from geodataframe
        graph_complex = nut.graph_from_gdf(edges_complex, nodes, node_id="node_fid")
        logging.info("Function [graph_from_gdf]: executed")
        return graph_complex, edges_complex

    def get_network(
        self,
        merge_lines: bool,
        snapping_threshold: bool,
        output_graph_dir: Path,
        project_name: str,
        segmentation_length: float,
    ):
        lines = self.read_merge_shp()

        # Check which of the lines are merged, also for the fid. The fid of the first line with a traffic count is taken.
        # The list of fid's is reduced by the fid's that are not anymore in the merged lines
        edges, lines_merged = lines, gpd.GeoDataFrame()
        if merge_lines:
            aadt_names = []
            edges, lines_merged = nut.merge_lines_automatic(
                lines, self.file_id, aadt_names, self.crs
            )
            logging.info(
                "Function [merge_lines_automatic]: executed with properties {}".format(
                    list(edges.columns)
                )
            )

        edges, id_name = nut.gdf_check_create_unique_ids(edges, self.file_id)

        if snapping_threshold:
            # TODO: snapping threshold it's a bool yet here we expect a float.
            edges = nut.snap_endpoints_lines(
                edges, snapping_threshold, id_name, self.crs
            )
            logging.info(
                "Function [snap_endpoints_lines]: executed with threshold = {}".format(
                    snapping_threshold
                )
            )

        # merge merged lines if there are any merged lines
        if not lines_merged.empty:
            # save the merged lines to a shapefile - CHECK if there are lines merged that should not be merged (e.g. main + secondary road)
            lines_merged.set_geometry(
                col="geometry", inplace=True
            )  # To ensure the object is a GeoDataFrame and not a Series
            _emerged_lines_file = output_graph_dir.joinpath(
                f"{project_name}_lines_that_merged.shp"
            )
            lines_merged.to_file(_emerged_lines_file)
            logging.info(
                "Function [edges_to_shp]: saved at {}".format(_emerged_lines_file)
            )

        graph_complex, edges_complex = self._get_complex_graph_and_edges(edges, id_name)

        if not math.isnan(segmentation_length):
            edges_complex = Segmentation(edges_complex, segmentation_length)
            edges_complex = edges_complex.apply_segmentation()
            if edges_complex.crs is None:  # The CRS might have dissapeared.
                edges_complex.crs = self.crs  # set the right CRS
        return graph_complex, edges_complex
