import logging
from pathlib import Path
from osgeo import gdal

from ra2ce.graph.networks_utils import bounds_intersect_2d, get_extent

def validate_extent_graph(extent_graph, tif_hazard_file: Path) -> None:
    """
    Validates the given extent graph to a hazard file (*.tif)

    Args:
        extent_graph (_type_): Graph to be validated.
        tif_hazard_file (Path): Hazard (*.tif) file.

    Raises:
        ValueError: When the hazard raster and the graph geometries do not overlap.
    """
    # Check if the hazard and graph extents overlap
    extent = get_extent(gdal.Open(str(tif_hazard_file)))
    extent_hazard = (
        extent["minX"],
        extent["maxX"],
        extent["minY"],
        extent["maxY"],
    )

    if not bounds_intersect_2d(extent_graph, extent_hazard):
        logging.info(
            "Raster extent: {}, Graph extent: {}".format(extent, extent_graph)
        )
        raise ValueError(
            "The hazard raster and the graph geometries do not overlap, check projection"
        )