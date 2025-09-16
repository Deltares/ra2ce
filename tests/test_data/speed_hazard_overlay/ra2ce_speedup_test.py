# Imports block
from pathlib import Path
import geopandas as gpd
import pytest
import rasterio
import time

from shapely.geometry import box

from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.ra2ce_handler import Ra2ceHandler

# Set path to hazard files 
cwd_path = Path.cwd()
test_data_path = cwd_path / 'tests' / 'test_data' / 'speed_hazard_overlay' 
hazard_files_dir = test_data_path / 'static' / 'hazard'
hazard_files = [file for file in hazard_files_dir.iterdir() if file.is_file()]
with rasterio.open(hazard_files[0]) as src:
    hazard_crs = src.crs
    extent = src.bounds

# Create shapefile of extent for OSM download
extent_gdf = gpd.GeoDataFrame(
    {'geometry': [box(extent.left, extent.bottom, extent.right, extent.top)]},
    crs=hazard_crs
)
extent_path = test_data_path / 'static' / 'network' / 'extent.shp'
extent_gdf.to_file(extent_path)


# RA2CE Config to download and process data from osm and overlay network with hazard raster
_network_section = NetworkSection(
    network_type=NetworkTypeEnum.DRIVE,
    source=SourceEnum.OSM_DOWNLOAD,
    polygon=extent_path, 
    save_gpkg=True,
    road_types=[RoadTypeEnum.MOTORWAY, RoadTypeEnum.MOTORWAY_LINK, RoadTypeEnum.PRIMARY, RoadTypeEnum.PRIMARY_LINK,RoadTypeEnum.TRUNK, RoadTypeEnum.SECONDARY,RoadTypeEnum.SECONDARY_LINK, RoadTypeEnum.TERTIARY, RoadTypeEnum.RESIDENTIAL, RoadTypeEnum.UNCLASSIFIED], 
)

_hazard_section = HazardSection(
    hazard_map=hazard_files,
    hazard_id=None,
    hazard_field_name="waterdepth",
    aggregate_wl=AggregateWlEnum.MAX,
    hazard_crs=hazard_crs,
    overlay_segmented_network = True
)

_network_config_data = NetworkConfigData(
    root_path=cwd_path,
    static_path=test_data_path / 'static',
    output_path=test_data_path / 'output',
    network=_network_section,
    hazard=_hazard_section)


# Setup timer
start_time = time.time()

# Run analysis
print('Starting RA2CE...')
_handler = Ra2ceHandler.from_config(_network_config_data, analysis=None)
_handler.configure()

end_time = time.time()
elapsed_time = end_time - start_time
print(f'Configuration completed in {elapsed_time:.2f} seconds.')

# Check results
# legacy_output_gdf = gpd.read_file('tests\test_data\speed_hazard_overlay\static\output_graph\base_graph_hazard_edges.gpkg')
legacy_output_gdf = gpd.read_file(test_data_path / 'static' / 'output_graph_legacy' / 'base_graph_hazard_edges.gpkg')
update_output_gdf = gpd.read_file(test_data_path / 'static' / 'output_graph' / 'base_graph_hazard_edges.gpkg')

print(f"EV1_ma values are equal before and after update: {legacy_output_gdf['EV1_ma'].values == pytest.approx(update_output_gdf['EV1_ma'].values)}")
print(f"EV1_fr values are equal before and after update: {legacy_output_gdf['EV1_fr'].values == pytest.approx(update_output_gdf['EV1_fr'].values)}")