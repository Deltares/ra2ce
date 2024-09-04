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

import rasterio
from networkx import Graph

from ra2ce.network.networks_utils import bounds_intersect_2d, get_extent


def validate_extent_graph(extent_graph: list[float], tif_hazard_file: Path) -> None:
    """
    Validates the given extent graph to a hazard file (*.tif)

    Args:
        extent_graph (list[float]): List of boundary points determening the extent of a graph.
        tif_hazard_file (Path): Hazard (*.tif) file.

    Raises:
        ValueError: When the hazard raster and the graph geometries do not overlap.
    """
    # Check if the hazard and graph extents overlap
    with rasterio.open(tif_hazard_file) as src:
        # Get the bounding box
        bounds = src.bounds

    # Extract the extent
    extent_hazard = (
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top,
    )

    if not bounds_intersect_2d(extent_graph, extent_hazard):
        logging.info("Raster extent: {}, Graph extent: {}".format(bounds, extent_graph))
        raise ValueError(
            "The hazard raster and the graph geometries do not overlap, check projection"
        )


def get_edges_geoms(graph: Graph) -> list:
    """
    Gets all edges geometry from a provided graph.
    """
    return [
        (u, v, k, edata)
        for u, v, k, edata in graph.edges.data(keys=True)
        if "geometry" in edata
    ]
