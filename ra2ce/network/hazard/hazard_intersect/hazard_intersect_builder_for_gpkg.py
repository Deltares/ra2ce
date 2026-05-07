"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023-2026 Stichting Deltares

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
from dataclasses import dataclass, field
from typing import Callable, List
from pathlib import Path

import numpy as np
from shapely.errors import TopologicalError
from shapely.geometry import MultiPolygon
from shapely.strtree import STRtree
from geopandas import GeoDataFrame, read_file
from networkx import Graph
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_base import (
    HazardIntersectBuilderBase,
)
from tqdm import tqdm


@dataclass
class HazardIntersectBuilderForGpkg(HazardIntersectBuilderBase):
    hazard_field_name: str = ""
    hazard_aggregate_wl: str = ""
    ra2ce_names: List[str] = field(default_factory=list)
    hazard_gpkg_files: List[Path] = field(default_factory=list)

    @staticmethod
    def _validate_and_fix_geometry(geometry):
        """Validate and fix invalid geometry using buffer(0). Return None if unfixable."""
        if not geometry.is_valid:
            try:
                geometry = geometry.buffer(0)
            except TopologicalError:
                return None
        return geometry if geometry.is_valid else None

    def _load_and_prepare_hazard(
        self, hazard_shp_file: Path, target_crs
    ) -> tuple[STRtree, list, list]:
        """Load hazard gpkg, reproject, explode, pre-validate geometries, and build STRtree.

        Returns:
            tree: STRtree built on the raw hazard geometries.
            hazard_geoms: pre-validated (and fixed) geometries, or None if unfixable.
            hazard_values: scalar hazard field values, one per exploded polygon.
        """
        gdf_hazard = read_file(str(hazard_shp_file))
        if gdf_hazard.crs != target_crs:
            gdf_hazard = gdf_hazard.to_crs(target_crs)

        logging.info("Converting MultiPolygon to Polygon")
        gdf_hazard_exploded = self._explode_multigeometries(gdf_hazard)

        raw_geoms = gdf_hazard_exploded.geometry.values
        # Pre-validate hazard geometries once; raw_geoms used for STRtree
        hazard_geoms = [self._validate_and_fix_geometry(g) for g in raw_geoms]
        hazard_values = gdf_hazard_exploded[self.hazard_field_name].tolist()
        tree = STRtree(raw_geoms)

        return tree, hazard_geoms, hazard_values

    def _compute_hazard_for_geometry(
        self,
        geom,
        tree: STRtree,
        hazard_geoms: list,
        hazard_values: list,
    ) -> tuple[float, float]:
        """Compute intersection fraction and aggregated hazard value for one network geometry.

        Returns:
            (intersection_fraction, hazard_value) — both 0 if no intersection.
        """
        geom = self._validate_and_fix_geometry(geom)
        if geom is None or geom.length == 0:
            return 0, 0

        total_length = geom.length
        intersection_length = 0.0
        intersected_values = []

        for idx in tree.query(geom):
            poly = hazard_geoms[idx]
            if poly is None or not geom.intersects(poly):
                continue
            intersection = geom.intersection(poly)
            if not intersection.is_empty:
                intersection_length += intersection.length
            val = hazard_values[idx]
            if val != 0:
                intersected_values.append(val)

        if intersection_length == 0:
            return 0, 0

        fraction = intersection_length / total_length
        agg_func = {"max": max, "min": min, "mean": np.nanmean}.get(
            self.hazard_aggregate_wl, np.nanmean
        )
        hazard_value = agg_func(intersected_values) if intersected_values else 0

        return fraction, hazard_value

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
            tree, hazard_geoms, hazard_values = self._load_and_prepare_hazard(
                hazard_shp_file, _hazard_overlay.graph["crs"]
            )

            logging.info("Processing edges for hazard overlay")
            for u, v, k, edata in tqdm(
                _hazard_overlay.edges(data=True, keys=True),
                total=_hazard_overlay.number_of_edges(),
                desc="Processing Edges",
                unit="edge",
            ):
                if "geometry" not in edata:
                    continue
                fraction, hazard_value = self._compute_hazard_for_geometry(
                    edata["geometry"], tree, hazard_geoms, hazard_values
                )
                edata[f"{ra2ce_name}_{self.hazard_aggregate_wl[:2]}"] = hazard_value
                edata[f"{ra2ce_name}_fr"] = fraction

            return _hazard_overlay

        return self._overlay_hazard_files(
            overlay_func=networkx_overlay, hazard_overlay=hazard_overlay
        )

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame) -> GeoDataFrame:
        """Overlays the hazard gpkg file over the road segments GeoDataFrame."""

        def geodataframe_overlay(
            _hazard_overlay: GeoDataFrame, hazard_shp_file: Path, ra2ce_name: str
        ) -> GeoDataFrame:
            tree, hazard_geoms, hazard_values = self._load_and_prepare_hazard(
                hazard_shp_file, _hazard_overlay.crs
            )

            _hazard_overlay[f"{ra2ce_name}_fr"] = 0
            _hazard_overlay[f"{ra2ce_name}_{self.hazard_aggregate_wl[:2]}"] = 0

            logging.info("Processing geometries for hazard overlay")
            for idx, geom in tqdm(
                _hazard_overlay["geometry"].items(),
                total=len(_hazard_overlay),
                desc="Processing Geometries",
                unit="geom",
            ):
                if geom is None or geom.is_empty:
                    continue
                fraction, hazard_value = self._compute_hazard_for_geometry(
                    geom, tree, hazard_geoms, hazard_values
                )
                _hazard_overlay.at[idx, f"{ra2ce_name}_fr"] = fraction
                _hazard_overlay.at[
                    idx, f"{ra2ce_name}_{self.hazard_aggregate_wl[:2]}"
                ] = hazard_value

            return _hazard_overlay

        return self._overlay_hazard_files(
            hazard_overlay=hazard_overlay, overlay_func=geodataframe_overlay
        )

    def _overlay_hazard_files(
        self,
        overlay_func: Callable[[GeoDataFrame | Graph, Path, str], GeoDataFrame | Graph],
        hazard_overlay: GeoDataFrame | Graph,
    ) -> GeoDataFrame | Graph:
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
        exploded_gdf = gdf.explode(index_parts=False).reset_index(drop=True)
        exploded_gdf["polygon_id"] = range(1, len(exploded_gdf) + 1)
        return exploded_gdf
