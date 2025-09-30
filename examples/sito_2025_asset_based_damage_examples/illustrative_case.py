import geopandas as gpd
from pathlib import Path
import pyproj
import rasterio
from shapely.geometry import box as make_box
from shapely.ops import transform

from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (NetworkConfigData,NetworkSection,HazardSection,)
from ra2ce.ra2ce_handler import Ra2ceHandler
from ra2ce.analysis.damages.damages import AnalysisSectionDamages
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import RiskCalculationModeEnum
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum


root_dir = Path("illustrative_case")

assert root_dir.exists(), "root_dir not found."

static_path = root_dir.joinpath("static")
hazard_path =root_dir.joinpath("hazard")
polygon_path = static_path.joinpath("static")
output_path=root_dir.joinpath("output")

hazard_map = list(hazard_path.glob("*.tif"))
# Function to reproject geometry
def reproject_geometry(geom, src_crs, dst_crs):
    project = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True).transform
    return transform(project, geom)

# Process only the first raster file in the list
with rasterio.open(hazard_map[0]) as src:
    bbox = src.bounds
    bbox_polygon = make_box(bbox.left, bbox.bottom, bbox.right, bbox.top)  # Create bounding box
    src_crs = src.crs
    dst_crs = 4326

    if src_crs.to_string() != dst_crs:
        # Reproject the bounding box polygon to EPSG:4326
        bbox_polygon = reproject_geometry(bbox_polygon, src_crs, pyproj.CRS.from_epsg(dst_crs))
        print(f"Hazard Map {hazard_map[0]} is in the CRS: {src_crs}")
        print("Reprojected the polygon to EPSG:4326")

# Create a GeoDataFrame with the bounding box polygon
gdf_polygon = gpd.GeoDataFrame(index=[0], geometry=[bbox_polygon], crs=dst_crs)
gdf_polygon.to_file(static_path.joinpath("polygon.geojson"), driver='GeoJSON')


network_section = NetworkSection(
    network_type=NetworkTypeEnum.DRIVE,
    source=SourceEnum.OSM_DOWNLOAD, #download the network from OSM
    polygon=static_path.joinpath("polygon.geojson"), #introduce the study area's polygon that you made based on the extent of the flood maps above.
    save_gpkg=True,
    road_types=[        #determine the level of detail you want to introduce to your road network. Mind that having more detail in a large area will slow down OSM download speed.
        RoadTypeEnum.TERTIARY,
        RoadTypeEnum.TERTIARY_LINK,
        RoadTypeEnum.SECONDARY,
        RoadTypeEnum.SECONDARY_LINK,
        RoadTypeEnum.PRIMARY,
        RoadTypeEnum.PRIMARY_LINK,
        RoadTypeEnum.TRUNK,
        RoadTypeEnum.MOTORWAY,
        RoadTypeEnum.MOTORWAY_LINK,
    ],
)

hazard_section = HazardSection(
    hazard_map=[Path(file) for file in hazard_path.glob("*.tif")],
    aggregate_wl = AggregateWlEnum.MEAN,
    hazard_crs = "EPSG:4326",
)

network_config_data = NetworkConfigData(
    root_path=root_dir,
    static_path=static_path,
    output_path=output_path,
    network=network_section,
    hazard=hazard_section
)
network_config_data.network.save_gpkg = True

# specify the parameters for the damage analysis
damages_analysis = [AnalysisSectionDamages(
    name='damages_with_asset',
    analysis=AnalysisDamagesEnum.DAMAGES_WITH_ASSETS,
    event_type=EventTypeEnum.RETURN_PERIOD,
    damage_curve=DamageCurveEnum.MAN,
    risk_calculation_mode=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR,
    risk_calculation_year=5,
    save_csv=True,
    save_gpkg=True
)]

analysis_config_data = AnalysisConfigData(
    analyses=damages_analysis,
    root_path=root_dir,
    input_path=Path.cwd().joinpath("input_data"),
    output_path=output_path,
)

analysis_config_data = AnalysisConfigData(analyses=damages_analysis, root_path=root_dir, output_path=output_path)
analysis_config_data.input_path = root_dir.joinpath("input_data")

Ra2ceHandler.run_with_config_data(network_config_data, analysis_config_data)