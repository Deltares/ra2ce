# Script to prepare the exposure data for the hackathon
import json
from pathlib import Path

import numpy as np
import rasterio
from shapely.geometry import box, mapping

root_dir = Path(r"/")
assert root_dir.exists()

static_path = root_dir.joinpath("static")
floodmap_path = root_dir.joinpath("hazard_files")
network_path = static_path.joinpath("network")
network_path.mkdir(exist_ok=True, parents=True)


def to_geojson(geometry: box, file_path: Path, indent=None, **kwargs):
    geojson = mapping(geometry)
    with open(file_path, "w") as f:
        json.dump(geojson, f, indent=indent, **kwargs)


# Loop over hazard maps to define the extent of the study area polygon
_extents: np.ndarray = np.empty((0, 4))
for _map in floodmap_path.glob("*.tif*"):
    with rasterio.open(_map) as _m:
        _extents = np.vstack(
            (
                _extents,
                np.array(
                    (_m.bounds.left, _m.bounds.bottom, _m.bounds.right, _m.bounds.top)
                ),
            ),
        )
_mins = np.min(_extents, axis=0)
_maxs = np.max(_extents, axis=0)

_min_lon = _mins[0]
_min_lat = _mins[1]
_max_lon = _maxs[2]
_max_lat = _maxs[3]

_extent_polygon = box(_min_lon, _min_lat, _max_lon, _max_lat)
to_geojson(_extent_polygon, network_path.joinpath("extent_polygon.geojson"))

# Create stretched polygons for OD (5% buffer) and network (10% buffer)
_od_polygon = _extent_polygon.buffer(
    ((_max_lon - _min_lon) * 0.05), quad_segs=4, cap_style="square"
)
to_geojson(_od_polygon, network_path.joinpath("buffer_polygon_OD.geojson"))

_network_polygon = _extent_polygon.buffer(((_max_lon - _min_lon) * 0.1))
to_geojson(_network_polygon, network_path.joinpath("buffer_polygon_network.geojson"))
