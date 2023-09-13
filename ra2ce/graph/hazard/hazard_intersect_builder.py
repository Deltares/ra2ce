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
import time
from typing import Union, Protocol
import geopandas as gpd
import networkx as nx


class HazardIntersectProtocol(Protocol):
    def get_hazard_intersect_from_tif(self, hazard_overlay):
        pass

    def get_hazard_intersect_from_shp(self, hazard_overlay):
        pass

    def get_hazard_intersect_from_table(self, hazard_overlay):
        pass


class GeoDataFrameHazardIntersect(HazardIntersectProtocol):
    def get_hazard_intersect_from_tif(self, hazard_overlay):
        """Logic to find the right hazard overlay function for the input to_overlay.

        Args:
            to_overlay (GeoDataFrame or NetworkX graph): Data that needs to be overlayed with a or multiple hazard maps.

        Returns:
            to_overlay (GeoDataFrame or NetworkX graph): The same data as input but with hazard values.

        The hazard file paths are in self.hazard_files.
        """
        start = time.time()
        to_overlay = self.overlay_hazard_raster_gdf(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_from_shp(self, hazard_overlay):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_gdf(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_from_table(self, hazard_overlay):
        start = time.time()
        to_overlay = self.join_hazard_table_gdf(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay


class NetworkxHazardIntersect(HazardIntersectProtocol):
    def get_hazard_intersect_from_tif(
        self, hazard_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.overlay_hazard_raster_graph(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard raster intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_from_shp(
        self, hazard_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.overlay_hazard_shp_graph(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard shapefile intersect time: {str(round(end - start, 2))}s")
        return to_overlay

    def get_hazard_intersect_from_table(
        self, hazard_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ):
        start = time.time()
        to_overlay = self.join_hazard_table_graph(hazard_overlay)
        end = time.time()
        logging.info(f"Hazard table intersect time: {str(round(end - start, 2))}s")
        return to_overlay


class HazardIntersectBuilder:
    @staticmethod
    def get_builder(
        hazard_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph]
    ) -> HazardIntersectProtocol:
        if isinstance(hazard_overlay, gpd.GeoDataFrame):
            return GeoDataFrameHazardIntersect()
        elif isinstance(hazard_overlay, nx.classes.graph.Graph):
            return NetworkxHazardIntersect()
        raise ValueError(
            "Overlay type {} not supported".format(type(hazard_overlay).__name__)
        )

    @staticmethod
    def build_intersection(
        hazard_files: list[Path],
        hazard_overlay: Union[gpd.GeoDataFrame, nx.classes.graph.Graph],
    ):
        _builder = HazardIntersectBuilder.get_builder(hazard_overlay)

        if hazard_files["tif"]:
            return _builder.get_hazard_intersect_from_tif(hazard_overlay)
        elif hazard_files["shp"]:
            return _builder.get_hazard_intersect_from_shp(hazard_overlay)
        elif hazard_files["table"]:
            return _builder.get_hazard_intersect_from_table(hazard_overlay)

        _files_formats = ",".join(hazard_files.keys())
        raise ValueError(
            "Hazard files format(s) not supported {}".format(_files_formats)
        )
