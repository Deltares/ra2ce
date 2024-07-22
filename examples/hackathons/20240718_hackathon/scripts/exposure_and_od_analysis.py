from pathlib import Path

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
from ra2ce.network import RoadTypeEnum
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
)
from ra2ce.ra2ce_handler import Ra2ceHandler
from ra2ce.ra2ce_logger import Ra2ceLogger

# Initialize console logger
Ra2ceLogger.initialize_console_logger("cloud_run_logger")

# Definition of paths
# Base Model
_root_dir = Path("/exposure_and_od_analysis")
# Override root location when running in local machine.
# aux_root = Path(__file__).parent.parent
# _root_dir = aux_root
_static_path = _root_dir.joinpath("static")
_base_graph_dir = _static_path.joinpath("output_graph")

_output_path = _root_dir.joinpath("output")
_output_path.mkdir(parents=True, exist_ok=True)
_results_to_collect = _output_path.joinpath("multi_link_origin_closest_destination")
network_polygon_file = _static_path.joinpath("network", "buffer_polygon_OD.geojson")


# Hazard files
_hazard_files = list(_root_dir.joinpath("hazard_files").glob("*.tif"))
print(f"Hazard files found: {len(_hazard_files)}")
_selected_hazard_file = _hazard_files[0]
print(f"Selected file: {_selected_hazard_file}")
assert _selected_hazard_file.is_file()

# THIS PROJECTION IS REQUIRED FOR THE HACKATHON JULY 2024
_hazard_crs = "EPSG:4326"


# Loop?
# Make the NetworkConfigData
_hazard_section = HazardSection(
    hazard_map=[_selected_hazard_file],
    hazard_id=None,
    hazard_field_name="waterdepth",
    aggregate_wl=AggregateWlEnum.MAX,
    hazard_crs=_hazard_crs,
    overlay_segmented_network=False,
)

_origin_destination_section = OriginsDestinationsSection(
    origins=_static_path.joinpath("network", "origins.shp"),
    destinations=_static_path.joinpath("network", "destinations.shp"),
    origins_names="A",
    destinations_names="B",
    id_name_origin_destination="ID",
    origin_count="POPULATION",
    origin_out_fraction=1,
    category="category",
)


_network_section = NetworkSection(
    source=SourceEnum.OSM_DOWNLOAD,  # Used to specify the shapefile name of the (road) network to do the analysis with, when creating a network from a shapefile.
    polygon=network_polygon_file,
    save_gpkg=True,
    road_types=[
        RoadTypeEnum.RESIDENTIAL,
        RoadTypeEnum.TERTIARY,
        RoadTypeEnum.UNCLASSIFIED,
        RoadTypeEnum.SECONDARY,
        RoadTypeEnum.PRIMARY,
        RoadTypeEnum.TRUNK,
        RoadTypeEnum.MOTORWAY,
    ],
)

_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=_static_path,
    output_path=_output_path,
    hazard=_hazard_section,
    network=_network_section,
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


# Read graphs with built-in functionality.
_graph_files = GraphFilesCollection.set_files(_base_graph_dir)
print("Loaded graph files. {}".format(print(_graph_files.__dict__)))

_handler = Ra2ceHandler.run_with_config_data(
    _network_config_data, _analysis_config_data
)

# Run analysis
_handler.input_config.network_config.graph_files = _graph_files
_handler.configure()
_handler.run_analysis()


# Verify results
# assert _results_to_collect.exists()
# assert any(list(_results_to_collect.glob("*_with_hazard.gpkg")))

_found_files = list(_results_to_collect.rglob("*"))
for _ff in _found_files:
    print(_ff)
_dummy_result_file = _results_to_collect.joinpath("dummy_file.txt")
_dummy_result_file.write_text("\n".join(list(map(str, _found_files))), encoding="utf-8")
