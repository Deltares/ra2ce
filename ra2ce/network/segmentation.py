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
import math
from decimal import Decimal
from typing import Optional, Union

import geopandas as gpd
from geopy import distance
from shapely.geometry import LineString, MultiLineString, Point

from ra2ce.network.networks_utils import cut as network_cut
from ra2ce.network.networks_utils import line_length


class Segmentation:  # Todo: more naturally, this would be METHOD of the network class.
    """cut the edges in the complex geodataframe to segments of equal lengths or smaller
    # output will be the cut edges_complex

    Variables:
        *self.edges_input* (Geopandas DataFrame) : the edges that are to be segmented
        *self.segmentation_length* (float) : segmentation length in metres
        *self.save_files* (Boolean) : save segmented graph?

    Result:
        *self.edges_segmented* (Geopandas DataFrame) : the segmented edges dataframe


    """

    @staticmethod
    def segment_graph(
        segmentation_length: float,
        crs: float,
        edges: gpd.GeoDataFrame,
        export_link_table: bool,
        link_tables: Optional[tuple] = None,
    ) -> Union[gpd.GeoDataFrame, tuple[gpd.GeoDataFrame, tuple]]:
        """
        Segments a complex graph based on the given segmentation length.

        Args:
        - segmentation_length (Optional[float]): The length to segment the graph edges. If None, no segmentation is applied.
        - edges_complex (gpd.GeoDataFrame): The GeoDataFrame containing the complex graph edges.
        - crs (str): The coordinate reference system to apply if the CRS is missing after segmentation.

        Returns:
        - gpd.GeoDataFrame: The segmented edges_complex GeoDataFrame.
        """
        if not math.isnan(segmentation_length):
            segmentation = Segmentation(edges, segmentation_length)
            segmented_edges = segmentation.apply_segmentation()
            if segmented_edges.crs is None:  # The CRS might have disappeared.
                segmented_edges.crs = crs  # set the right CRS

            if export_link_table:
                updated_link_tables = segmentation.generate_link_tables()
                segmented_edges.drop(columns=["rfid_c"], inplace=True)
                segmented_edges.rename(columns={"splt_id": "rfid_c"}, inplace=True)
                return segmented_edges, updated_link_tables
            return segmented_edges
        elif export_link_table and link_tables:
            return edges, link_tables
        elif export_link_table and not link_tables:
            logging.warning("empty link_tables is passed")
            return edges, tuple()
        else:
            return edges

    def __init__(
        self,
        edges_input: gpd.GeoDataFrame,
        segmentation_length: float,
        save_files: bool = False,
    ):
        # General
        self.edges_input = edges_input  # Edges GeoDataFrame
        self.edges_segmented = (
            None  # This is where the result will be saved Edges GeoDataframe
        )
        self.link_tables = (
            None  # will include dictionaries simple_ids to complex and vice-versa
        )
        self._get_segmentation_length_from_metre(segmentation_length)
        self.save_files = save_files  # Todo not implemented yet

    def _get_segmentation_length_from_metre(self, segmentation_length_in_metre: float):
        """
        Convert a length in meters to degrees at a given latitude.

        Args:
        - segmentation_length_in_metre: Length in meters to be converted.
        """

        origin = (
            0,
            0,
        )  # reference at the equator. The conversion is more accurate at the equator and changes as you move towards the poles.

        # Calculate the destination point segmentation_length_in_metre north (latitude direction)
        try:
            distance.geodesic.ELLIPSOID = self.edges_input.crs.ellipsoid.name.replace(
                " ", "-"
            )
        except:
            distance.geodesic.ELLIPSOID = "WGS-84"

        destination_point_lat = distance.geodesic(
            meters=segmentation_length_in_metre
        ).destination(origin, bearing=0)

        self.segmentation_length = (
            destination_point_lat.latitude - origin[0]
        )  # length in degrees

    def apply_segmentation(self) -> gpd.GeoDataFrame:
        self.cut_gdf()
        logging.info(
            "Finished segmenting the geodataframe with split length: {} degree".format(
                self.segmentation_length
            )
        )
        return self.edges_segmented

    def cut(self, line: LineString, distance: float) -> list:
        """Cuts a line in two at a distance from its starting point

        Args:
            line (LineString): Single linestring.
            distance (float): Distance from starting point of linestring

        Returns:
            (list): A list containing two shapely linestring objects.
        """

        if distance <= 0.0 or distance >= line.length:
            return [LineString(line)]
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
            if pd == distance:
                return [LineString(coords[: i + 1]), LineString(coords[i:])]
            if pd > distance:
                cp = line.interpolate(distance)
                return [
                    LineString(coords[:i] + [(cp.x, cp.y)]),
                    LineString([(cp.x, cp.y)] + coords[i:]),
                ]

    def check_divisibility(self, dividend, divisor):
        """Checks if the dividend is a multiple of the divisor and outputs a boolean value

        Args:
            dividend (float): The number which is divided
            divisor (float): The number which divides

        Returns:
            is_multiple (bool): True if the dividend is a multiple of the divisor, False if not
        """

        dividend = Decimal(str(dividend))
        divisor = Decimal(str(divisor))
        remainder = dividend % divisor

        return remainder == Decimal("0")

    def number_of_segments(self, linestring: LineString, split_length: float) -> int:
        """Returns the integer number of segments which will result from chopping up a linestring with split_length

        Args:
            linestring (LineString): Single linestring.
            split_length (float): The length by which to divide the linestring object.

        Returns:
            n (int): Integer number of segments which will result from splitting linestring with split_length.
        """

        divisible = self.check_divisibility(linestring.length, split_length)
        if divisible:
            return int(linestring.length / split_length)
        return int(linestring.length / split_length) + 1

    def split_linestring(self, linestring: LineString, split_length: float):
        """Cuts a linestring in equivalent segments of length split_length

        Args:
            linestring (LineString): Single linestring.
            split_length (float): Length by which to split the linestring into equal segments.

        Returns:
            result_list (list): list of LineString objects that all have the same length split_lenght.
        """

        n_segments = self.number_of_segments(linestring, split_length)
        if n_segments != 1:
            result_list = [None] * n_segments
            current_right_linestring = linestring

            for i in range(0, n_segments - 1):
                r = network_cut(current_right_linestring, split_length)
                # Can accidently return Nonetypes
                if r is not None:
                    current_left_linestring = r[0]
                    current_right_linestring = r[1]
                    result_list[i] = current_left_linestring
                    result_list[i + 1] = current_right_linestring
                # Sometimes the remainder is so small that it is only one point, which cannot be cut, in that case
                # just pass #Todo: maybe we can do something here to avoid this error

        else:
            result_list = [linestring]

        # Make sure this  function does not return any None objects, because these will cause problems later
        result_list = [
            x
            for x in result_list
            if (type(x) == LineString or type(x) == MultiLineString)
        ]

        return result_list

    def cut_gdf(self):
        """
        Cuts every linestring or multilinestring feature in a gdf to equal length segments. Assumes only linestrings for now.

            *gdf* (GeoDataFrame) : GeoDataFrame to split
            *length* (units of the projection) : Typically in degrees, 0.001 degrees ~ 111 m in Europe
        """
        gdf = self.edges_input.copy()
        columns = gdf.columns

        data = {"splt_id": []}

        for column in columns:
            data[column] = []

        count = 1
        for _, row in gdf.iterrows():
            geom = row["geometry"]
            assert type(geom) == LineString or type(geom) == MultiLineString
            linestrings = self.split_linestring(geom, self.segmentation_length)

            for _, linestring in enumerate(linestrings):
                for key, value in row.items():
                    if key == "geometry":
                        data[key].append(linestring)
                    elif key == "length":
                        data[key].append(line_length(linestring, self.edges_input.crs))
                    elif key == "time":
                        data[key].append(
                            round((row["length"] / row["avgspeed"]) / 1000, 5)
                        )
                    else:
                        data[key].append(value)
                data["splt_id"].append(count)
                count += 1
        self.edges_segmented = gpd.GeoDataFrame(data)

    def generate_link_tables(
        self,
    ) -> tuple[dict[int, Union[int, list[int]]], dict[int, int]]:
        """
        Generate mappings from a GeoDataFrame and two dictionaries.

        Args:
        - dicts: Tuple of two dictionaries.
            - First dictionary maps rfid to rfid_c (integer or list of integers).
            - Second dictionary maps rfid_c to rfid (integer).

        Returns:
        - A tuple containing two dictionaries:
            - The first dictionary maps rfid to splt_id or list of splt_id.
            - The second dictionary maps splt_id to rfid.
        """
        # Initialize result dictionaries
        splt_id_to_rfid = {}
        rfid_to_splt_id = {}

        # Create a mapping from splt_id to rfid
        for _, row in self.edges_segmented.iterrows():
            splt_id = row["splt_id"]
            rfid = row["rfid"]
            splt_id_to_rfid[splt_id] = rfid

        # Create a mapping from rfid to splt_id
        for _, row in self.edges_segmented.iterrows():
            splt_id = row["splt_id"]
            rfid = row["rfid"]
            rfid_c = row["rfid_c"]

            # Determine the expected rfid from rfid_c
            if rfid in rfid_to_splt_id:
                if isinstance(rfid_to_splt_id[rfid], list):
                    rfid_to_splt_id[rfid].append(splt_id)
                else:
                    rfid_to_splt_id[rfid] = [rfid_to_splt_id[rfid], splt_id]
            else:
                rfid_to_splt_id[rfid] = splt_id

        # Sort the dictionaries by their keys
        splt_id_to_rfid_sorted = dict(sorted(splt_id_to_rfid.items()))
        rfid_to_splt_id_sorted = dict(sorted(rfid_to_splt_id.items()))
        self.link_tables = (rfid_to_splt_id_sorted, splt_id_to_rfid_sorted)
        return self.link_tables
