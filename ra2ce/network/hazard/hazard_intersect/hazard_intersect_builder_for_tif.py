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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from geopandas import GeoDataFrame
from networkx import Graph, set_edge_attributes
from numpy import nan
from rasterstats import zonal_stats
from tqdm import tqdm

from ra2ce.network.hazard.hazard_common_functions import (
    get_edges_geoms,
    validate_extent_graph,
)
from ra2ce.network.hazard.hazard_intersect.hazard_intersect_builder_base import (
    HazardIntersectBuilderBase,
)
from ra2ce.network.networks_utils import (
    fraction_flooded,
    get_graph_edges_extent,
    get_valid_mean,
)


@dataclass
class HazardIntersectBuilderForTif(HazardIntersectBuilderBase):
    hazard_aggregate_wl: str = ""
    hazard_names: list[str] = field(default_factory=list)
    ra2ce_names: list[str] = field(default_factory=list)
    hazard_tif_files: list[Path] = field(default_factory=list)

    @property
    def _combined_names(self) -> list[tuple[str, str]]:
        """
        Combines into tuples `hazard_names` and `ra2ce_names`.

        Returns:
            list[tuple[str, str]]: List of `str` tuples (hazard_name, ra2ce_name).
        """
        return list(zip(self.hazard_names, self.ra2ce_names))

    def _from_networkx(self, hazard_overlay: Graph) -> Graph:
        """Overlays the hazard raster over the road segments graph.

        Args:
            *hf* (list of Pathlib paths) : #not sure if this is needed as argument if we also read if from the config
            *graph* (NetworkX Graph) : NetworkX graph with geometries that will be intersected with the hazard map raster.

        Returns:
            *graph* (NetworkX Graph) : NetworkX graph with hazard values
        """
        # TODO apply multiprocessing?
        # from tqdm import (
        #     tqdm,  # somehow this only works when importing here and not at the top of the file
        # )

        # Verify the graph type (networkx)
        assert isinstance(hazard_overlay, Graph)
        extent_graph = get_graph_edges_extent(hazard_overlay)

        # Get all edge geometries
        edges_geoms = get_edges_geoms(hazard_overlay)

        def overlay_network_x(hazard_tif_file: Path, hazard_name: str, ra2ce_name: str):
            # Check if the hazard and graph extents overlap
            validate_extent_graph(extent_graph, hazard_tif_file)
            # Add a no-data value for the edges that do not have a geometry
            set_edge_attributes(
                hazard_overlay,
                {
                    (u, v, k): {ra2ce_name + "_" + self.hazard_aggregate_wl[:2]: nan}
                    for u, v, k, edata in hazard_overlay.edges.data(keys=True)
                    if "geometry" not in edata
                },
            )

            # Add the hazard values to the edges that do have a geometry
            gdf = GeoDataFrame(
                {"geometry": [edata["geometry"] for u, v, k, edata in edges_geoms]}
            )
            tqdm.pandas(desc="Graph hazard overlay with " + hazard_name)
            _tif_hazard_files = str(hazard_tif_file)
            if self.hazard_aggregate_wl == "mean":
                flood_stats = gdf.geometry.progress_apply(
                    lambda x, _files_value=_tif_hazard_files: zonal_stats(
                        x,
                        _files_value,
                        all_touched=True,
                        add_stats={"mean": get_valid_mean},
                    )
                )
            else:
                flood_stats = gdf.geometry.progress_apply(
                    lambda x, _files_value=_tif_hazard_files: zonal_stats(
                        x,
                        _files_value,
                        all_touched=True,
                        stats=f"{self.hazard_aggregate_wl}",
                    )
                )

            try:
                flood_stats = flood_stats.apply(
                    lambda x: (
                        x[0][self.hazard_aggregate_wl]
                        if x[0][self.hazard_aggregate_wl]
                        else 0
                    )
                )
                set_edge_attributes(
                    hazard_overlay,
                    {
                        (edges[0], edges[1], edges[2]): {
                            ra2ce_name + "_" + self.hazard_aggregate_wl[:2]: x
                        }
                        for x, edges in zip(flood_stats, edges_geoms)
                    },
                )
            except KeyError:
                logging.warning(
                    "No aggregation method ('aggregate_wl') is chosen - choose from 'max', 'min' or 'mean'."
                )

            # Get the fraction of the road that is intersecting with the hazard
            tqdm.pandas(desc="Graph fraction with hazard overlay with " + hazard_name)
            graph_fraction_flooded = gdf.geometry.progress_apply(
                lambda x, _files_values=_tif_hazard_files: fraction_flooded(
                    x, _files_values
                )
            )
            graph_fraction_flooded = graph_fraction_flooded.fillna(0)
            set_edge_attributes(
                hazard_overlay,
                {
                    (edges[0], edges[1], edges[2]): {ra2ce_name + "_fr": x}
                    for x, edges in zip(graph_fraction_flooded, edges_geoms)
                },
            )

        self._overlay_hazard_files(overlay_network_x)
        return hazard_overlay

    def _from_geodataframe(self, hazard_overlay: GeoDataFrame):
        """Overlays the hazard raster over the road segments GeoDataFrame.

        Args:
            *graph* (GeoDataFrame) : GeoDataFrame that will be intersected with the hazard map raster.

        Returns:

        """
        assert isinstance(hazard_overlay, GeoDataFrame), "Network is not a GeoDataFrame"

        # Make sure none of the geometries is a nonetype object (this will raise an error in zonal_stats)
        empty_entries = hazard_overlay.loc[hazard_overlay.geometry.isnull()]
        if any(empty_entries):
            logging.warning(
                (
                    "Some geometries have NoneType objects (no coordinate information), namely: {}.".format(
                        empty_entries
                    )
                    + "This could be due to segmentation, and might cause an exception in hazard overlay"
                )
            )

        def overlay_geodataframe(
            hazard_tif_file: Path, hazard_name: str, ra2ce_name: str
        ):
            # Validate input
            # Check if network and raster overlap
            extent_graph = (
                hazard_overlay.total_bounds[0],
                hazard_overlay.total_bounds[2],
                hazard_overlay.total_bounds[1],
                hazard_overlay.total_bounds[3],
            )
            validate_extent_graph(extent_graph, hazard_tif_file)

            tqdm.pandas(desc="Network hazard overlay with " + hazard_name)
            _hazard_files_str = str(hazard_tif_file)
            # Performance sinkhole
            flood_stats = hazard_overlay.geometry.progress_apply(
                lambda _geom_vector: zonal_stats(
                    vectors=_geom_vector,
                    raster=_hazard_files_str,
                    all_touched=True,
                    stats="min max",
                    add_stats={"mean": get_valid_mean},
                )
            )

            def _get_attributes(gen_flood_stat: list[dict]) -> tuple:
                # Just get the first element of the generator
                _flood_stat = gen_flood_stat[0]
                return _flood_stat["min"], _flood_stat["max"], _flood_stat["mean"]

            (
                hazard_overlay[ra2ce_name + "_mi"],
                hazard_overlay[ra2ce_name + "_ma"],
                hazard_overlay[ra2ce_name + "_me"],
            ) = list(zip(*map(_get_attributes, flood_stats)))

            tqdm.pandas(desc="Network fraction with hazard overlay with " + hazard_name)
            hazard_overlay[ra2ce_name + "_fr"] = hazard_overlay.geometry.progress_apply(
                lambda x, _hz_str=_hazard_files_str: fraction_flooded(x, _hz_str)
            )

        self._overlay_hazard_files(overlay_geodataframe)
        return hazard_overlay

    def _overlay_hazard_files(self, overlay_func: Callable[[str, str, str], None]):
        for i, (hn, rn) in enumerate(self._combined_names):
            overlay_func(self.hazard_tif_files[i], hn, rn)
