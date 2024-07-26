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

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, List
from pathlib import Path
from shapely.geometry import MultiPolygon, Polygon
from shapely.strtree import STRtree
from numpy import nanmean
from geopandas import GeoDataFrame, read_file
from networkx import Graph
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_base import (
    HazardIntersectBuilderBase,
)


@dataclass
class HazardIntersectBuilderForGpkg(HazardIntersectBuilderBase):
    hazard_field_name: str = ""
    hazard_aggregate_wl: str = ""
    ra2ce_names: List[str] = field(default_factory=list)
    hazard_gpkg_files: List[Path] = field(default_factory=list)

    def _from_networkx(self, hazard_overlay: Graph) -> Graph:
        """Overlays the hazard `gpkg` file over the road segments NetworkX graph.

        Args:
            hazard_overlay (NetworkX graph): The graph that should be overlaid with the hazard `gpkg` file(s).

        Returns:
            hazard_overlay (NetworkX graph): The graph with hazard shapefile(s) data joined
        """

        def networkx_overlay(
            _hazard_overlay: Graph, hazard_shp_file: Path, ra2ce_name: str
        ) -> Graph:
            def process_edge(_u, _v, _k, _edata):
                if "geometry" in _edata:
                    total_length = _edata["geometry"].length
                    if total_length == 0:
                        return 0, 0

                    possible_matches_indices = tree.query(_edata["geometry"])
                    intersection_length = sum(
                        _edata["geometry"].intersection(poly).length
                        for idx in possible_matches_indices
                        for poly in (
                            hazard_geoms[idx].geoms
                            if isinstance(hazard_geoms[idx], MultiPolygon)
                            else [hazard_geoms[idx]]
                        )
                        if _edata["geometry"].intersects(poly)
                        and gdf_hazard_exploded.iloc[idx][self.hazard_field_name] != 0
                    )
                    _intersection_fraction = intersection_length / total_length

                    intersected_values = [
                        gdf_hazard_exploded.iloc[idx][self.hazard_field_name]
                        for idx in possible_matches_indices
                        if _edata["geometry"].intersects(hazard_geoms[idx])
                        and gdf_hazard_exploded.iloc[idx][self.hazard_field_name] != 0
                    ]

                    if intersected_values:
                        if self.hazard_aggregate_wl == "max":
                            _hazard_value = max(intersected_values)
                        elif self.hazard_aggregate_wl == "min":
                            _hazard_value = min(intersected_values)
                        elif self.hazard_aggregate_wl == "mean":
                            _hazard_value = nanmean(intersected_values)
                    else:
                        _hazard_value = 0

                    return _intersection_fraction, _hazard_value
                else:
                    return 0, 0

            gdf_hazard = read_file(str(hazard_shp_file))

            if _hazard_overlay.graph["crs"] != gdf_hazard.crs:
                gdf_hazard = gdf_hazard.to_crs(_hazard_overlay.graph["crs"])

            # Convert MultiPolygon to Polygon
            gdf_hazard_exploded = self._explode_multigeometries(gdf_hazard)

            tree = STRtree(gdf_hazard_exploded["geometry"].tolist())
            hazard_geoms = gdf_hazard_exploded.geometry.values

            with ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(
                        lambda edge: process_edge(*edge),
                        _hazard_overlay.edges(data=True, keys=True),
                    )
                )

            for (u, v, k, edata), (intersection_fraction, hazard_value) in zip(
                _hazard_overlay.edges(data=True, keys=True), results
            ):
                edata[ra2ce_name + "_" + self.hazard_aggregate_wl[:2]] = hazard_value
                edata[ra2ce_name + "_" + "fr"] = intersection_fraction

            return _hazard_overlay

        hazard_overlay = self._overlay_hazard_files(
            overlay_func=networkx_overlay, hazard_overlay=hazard_overlay
        )

        return hazard_overlay

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame) -> GeoDataFrame:
        """Overlays the hazard shapefile over the road segments GeoDataFrame."""

        gdf_crs_original = hazard_overlay.crs

        def geodataframe_overlay(
            _hazard_overlay: GeoDataFrame, hazard_shp_file: Path, ra2ce_name: str
        ) -> GeoDataFrame:
            gdf_hazard = read_file(str(hazard_shp_file))

            if _hazard_overlay.crs != gdf_hazard.crs:
                _hazard_overlay = _hazard_overlay.to_crs(gdf_hazard.crs)

            # Convert MultiPolygon to Polygon
            gdf_hazard_exploded = self._explode_multigeometries(gdf_hazard)
            tree = STRtree(gdf_hazard_exploded["geometry"].tolist())

            intersected_fractions = []
            hazard_values_list = []
            hazard_geoms = gdf_hazard_exploded["geometry"].values

            def calculate_intersection_fraction(line):
                total_length = line.length
                if total_length == 0:
                    return 0, []

                possible_matches_indices = list(tree.query(line))
                intersection_length = sum(
                    line.intersection(hazard_geoms[idx]).length
                    for idx in possible_matches_indices
                    if line.intersects(hazard_geoms[idx])
                )
                intersection_fraction = intersection_length / total_length

                _intersected_values = [
                    gdf_hazard_exploded.iloc[idx][self.hazard_field_name]
                    for idx in possible_matches_indices
                    if line.intersects(hazard_geoms[idx])
                    and gdf_hazard_exploded.iloc[idx][self.hazard_field_name] != 0
                ]

                return intersection_fraction, _intersected_values

            # Using ThreadPoolExecutor for parallel processing
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(
                        calculate_intersection_fraction, _hazard_overlay["geometry"]
                    )
                )

            for fraction, intersected_values in results:
                intersected_fractions.append(fraction)

                if intersected_values:
                    if self.hazard_aggregate_wl == "max":
                        hazard_value = max(intersected_values)
                    elif self.hazard_aggregate_wl == "min":
                        hazard_value = min(intersected_values)
                    elif self.hazard_aggregate_wl == "mean":
                        hazard_value = nanmean(intersected_values)
                else:
                    hazard_value = 0

                hazard_values_list.append(hazard_value)

            _hazard_overlay[ra2ce_name + "_" + "fr"] = intersected_fractions
            _hazard_overlay[ra2ce_name + "_" + self.hazard_aggregate_wl[:2]] = (
                hazard_values_list
            )

            return _hazard_overlay

        hazard_overlay_performed = self._overlay_hazard_files(
            hazard_overlay=hazard_overlay, overlay_func=geodataframe_overlay
        )

        if hazard_overlay_performed.crs != gdf_crs_original:
            hazard_overlay_performed = hazard_overlay_performed.to_crs(gdf_crs_original)

        return hazard_overlay_performed

    def _overlay_hazard_files(
        self,
        overlay_func: Callable[[GeoDataFrame | Graph, Path, str], GeoDataFrame | Graph],
        hazard_overlay: GeoDataFrame | Graph,
    ) -> GeoDataFrame:
        for i, ra2ce_name in enumerate(self.ra2ce_names):
            hazard_overlay = overlay_func(
                _hazard_overlay=hazard_overlay,
                hazard_shp_file=self.hazard_gpkg_files[i],
                ra2ce_name=ra2ce_name,
            )
        return hazard_overlay

    def _explode_multigeometries(self, gdf: GeoDataFrame) -> GeoDataFrame:
        """Convert MultiPolygon geometries in a GeoDataFrame to individual Polygon geometries.

        Args:
            gdf (GeoDataFrame): The input GeoDataFrame with MultiPolygon geometries.

        Returns:
            GeoDataFrame: A new GeoDataFrame with individual Polygon geometries.
        """

        def explode_geometry(_row):
            if isinstance(_row.geometry, MultiPolygon):
                return [Polygon(poly) for poly in _row.geometry.geoms]
            else:
                return [_row.geometry]

        # Explode MultiPolygon geometries
        exploded_geometries = []
        exploded_attributes = []
        for _, row in gdf.iterrows():
            exploded_geom = explode_geometry(row)
            for geom in exploded_geom:
                exploded_geometries.append(geom)
                exploded_attributes.append(row.drop("geometry"))

        exploded_gdf = GeoDataFrame(
            exploded_attributes, geometry=exploded_geometries, crs=gdf.crs
        )
        exploded_gdf["polygon_id"] = range(1, len(exploded_gdf) + 1)

        return exploded_gdf
