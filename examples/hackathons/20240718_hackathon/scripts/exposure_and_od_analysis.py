import pickle
from pathlib import Path

import geopandas as gpd

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionLosses,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.graph_files.network_file import NetworkFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    OriginsDestinationsSection,
)
from ra2ce.ra2ce_handler import Ra2ceHandler


# Functions
def read_pickle(file_path: str):
    """
    Read a pickle file.

    Args:
        file_path (str): The path to the pickle file.

    Returns:
        The object stored in the pickle file.
    """
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return data


def read_gpkg_to_gdf(file_path: str, layer: str = None) -> gpd.GeoDataFrame:
    """
    Read a GeoPackage file into a GeoDataFrame.

    Args:
        file_path (str): The path to the GeoPackage file.
        layer (str, optional): The specific layer to read from the GeoPackage. If None, reads the default layer.

    Returns:
        gpd.GeoDataFrame: The GeoDataFrame created from the GeoPackage file.
    """
    # Read the geopackage file into a GeoDataFrame
    gdf = gpd.read_file(file_path, layer=layer)

    return gdf


# Definition of paths
# Base Model
_root_dir = Path("/exposure_and_od_analysis")
_static_path = _root_dir.joinpath("static")
_base_graph_dir = _static_path.joinpath("output_graph")

_output_path = _root_dir.joinpath("output")
_output_path.mkdir(parents=True, exist_ok=True)

# Hazard files
_hazard_files = list(Path("/hazard_files").glob("*.tif"))
print("Hazard files found: " + len(_hazard_files))
_selected_hazard_file = _hazard_files[0]
hazard_crs = "EPSG:32736"  # for the hackathon case => "EPSG:4326"


# Loop?
# Make the NetworkConfigData
_hazard_section = HazardSection(
    hazard_map=[_selected_hazard_file],
    hazard_id=None,
    hazard_field_name="waterdepth",
    aggregate_wl=AggregateWlEnum.MAX,
    hazard_crs=hazard_crs,
    overlay_segmented_network=False,
)

_origin_destination_section = OriginsDestinationsSection(
    origins=_static_path.joinpath("network", "origins.shp"),
    destinations=_static_path.joinpath("network", "destinations.shp"),
    origins_names="A",
    destinations_names="B",
    id_name_origin_destination="OBJECTID",
    origin_count="POPULATION",
    origin_out_fraction=1,
    category="category",
)

_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=_static_path,
    output_path=_output_path,
    hazard=_hazard_section,
    origins_destinations=_origin_destination_section,
)
_network_config_data.network.save_gpkg = True

# Make the AnalysisConfigData
_analysis_section = AnalysisSectionLosses(
    name="origin_closest_destination",
    analysis=AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION,
    aggregate_wl=AggregateWlEnum.MAX,
    threshold=0.5,
    weighing=WeighingEnum.LENGTH,
    calculate_route_without_disruption=True,
    save_gpkg=True,
    save_csv=True,
)

_analysis_config_data = AnalysisConfigData(
    project=ProjectSection(name=_selected_hazard_file.stem),
    root_path=_root_dir,
    static_path=_static_path,
    output_path=_output_path,
    analyses=[_analysis_section],
)
_analysis_config_wrapper = AnalysisConfigWrapper()
_analysis_config_wrapper.config_data = _analysis_config_data
_analysis_config_data.hazard_names = HazardNames.from_config(_analysis_config_wrapper)


# Add the generated graphs
_graph_files = GraphFilesCollection(
    base_graph=GraphFile(
        name="base_graph",
        folder=_base_graph_dir,
        graph=read_pickle(_base_graph_dir.joinpath("base_graph.p")),
    ),
    base_network=NetworkFile(
        name="base_network",
        folder=_base_graph_dir,
        graph=read_gpkg_to_gdf(_base_graph_dir.joinpath("base_network.gpkg")),
    ),
    origins_destinations_graph=GraphFile(
        name="origins_destinations_graph",
        folder=_base_graph_dir,
        graph=read_pickle(_base_graph_dir.joinpath("origins_destinations_graph.p")),
    ),
)
_handler = Ra2ceHandler.from_config(_network_config_data, _analysis_config_data)

# Run analysis
_handler.input_config.network_config.graph_files = _graph_files
_handler.configure()
_handler.run_analysis()
