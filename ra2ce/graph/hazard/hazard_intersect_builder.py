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
