from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape

from ra2ce.network.exporters.geodataframe_network_exporter import (
    GeoDataFrameNetworkExporter,
)
from ra2ce.network.exporters.multi_graph_network_exporter import (
    MultiGraphNetworkExporter,
)
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.network_config_data import (
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_network_wrapper import (
    OsmNetworkWrapper,
)

root_dir = Path(r"/")
assert root_dir.exists()

static_path = root_dir.joinpath("static")
hazard_path = static_path.joinpath("hazard")
network_path = static_path.joinpath("network")

# Read the network extent
_polygon_path = network_path.joinpath("buffer_polygon_network.geojson")
assert _polygon_path.exists()

_polygon_gdf = gpd.read_file(_polygon_path)
_network_polygon = shape(_polygon_gdf.geometry.iloc[0])

# Create the network
_network_section = NetworkSection(
    network_type=NetworkTypeEnum.DRIVE,
    road_types=[
        RoadTypeEnum.MOTORWAY,
        RoadTypeEnum.MOTORWAY_LINK,
        RoadTypeEnum.PRIMARY,
        RoadTypeEnum.PRIMARY_LINK,
        RoadTypeEnum.TRUNK,
        RoadTypeEnum.SECONDARY,
        RoadTypeEnum.SECONDARY_LINK,
        RoadTypeEnum.TERTIARY,
        RoadTypeEnum.TERTIARY_LINK,
    ],
)
_network_config_data = NetworkConfigData(
    network=_network_section, static_path=static_path
)

_graph, _gdf = OsmNetworkWrapper.get_network_from_polygon(
    _network_config_data, _network_polygon
)

# Export the graph
_exporter = MultiGraphNetworkExporter(
    basename="base_graph", export_types=["gpkg", "pickle"]
)
_exporter.export(
    export_path=root_dir.joinpath("static", "output_graph"), export_data=_graph
)

# Export the network
_exporter = GeoDataFrameNetworkExporter(
    basename="base_network", export_types=["gpkg", "pickle"]
)
_exporter.export(
    export_path=root_dir.joinpath("static", "output_graph"), export_data=_gdf
)
