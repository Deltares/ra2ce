from pathlib import Path

import geopandas as gpd
import osmnx
from shapely.geometry import shape

root_dir = Path("/")
assert root_dir.exists()

static_path = root_dir.joinpath("static")
hazard_path = static_path.joinpath("hazard")
network_path = static_path.joinpath("network")

# Read the OD extent
_polygon_path = network_path.joinpath("buffer_polygon_OD.geojson")
assert _polygon_path.exists()

_polygon_gdf = gpd.read_file(_polygon_path)
_od_polygon = shape(_polygon_gdf.geometry.iloc[0])

# Download the destinations
_tags_basic_needs = {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]}
_features = osmnx.features_from_polygon(polygon=_od_polygon, tags=_tags_basic_needs)

_features["ID"] = range(len(_features))
_destinations = _features[["ID", "amenity", "name", "geometry"]]
_destinations.rename(columns={"amenity": "category"}, inplace=True)
_destinations["geometry"] = _destinations.geometry.apply(
    lambda geom: geom.representative_point()
)

_destinations.to_file(
    network_path.joinpath("Destinations.shp"), driver="ESRI Shapefile"
)
