import os
import random
import shutil
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.ra2ce_handler import Ra2ceHandler

# Define locations in mounted drive
_root_dir = Path("/modeldata")
_static_path = _root_dir.joinpath("static")
_static_output_graph_path = _root_dir.joinpath("static", "output_graph")
assert _root_dir.exists()
assert _static_path.exists()

for _file in _root_dir.rglob("*"):
    print(_file.relative_to(_root_dir))

# Graph with overlayed events
_output_graph = Path("/output_graph")
assert _output_graph.exists()

# Vulnerability curves
_vulnerability_curves = Path("/vulnerability_curves")
assert _vulnerability_curves.exists()

# Select a random vulnerability cuve
_selected_vulnerability_curve = random.choice(list(_vulnerability_curves.glob("*.csv")))
print(_selected_vulnerability_curve)

_results_dir = Path("/output_workflow2")
shutil.copytree(_root_dir, _results_dir.joinpath("base_model"))
shutil.copytree(_output_graph, _results_dir.joinpath("output_graph"))
shutil.copyfile(
    _selected_vulnerability_curve,
    _results_dir.joinpath("vulnerability_curve", _selected_vulnerability_curve.name),
)

# _tif_data_directory = Path("/flood_maps/event1")
# vc = _root_dir.joinpath("vulnerability_curves/damage_functions/all_road_types")


# # RA2CE RUN .......................................................................................
# # Replacement for network ini:
# _network_section = NetworkSection(
#     source=SourceEnum.SHAPEFILE,
#     primary_file=[_root_dir.joinpath("static", "network", "motorway_osm.shp")],
#     file_id="rfid_c",
#     save_gpkg=True,
# )

# # pass the specified sections as arguments for configuration
# _network_config_data = NetworkConfigData(
#     root_path=_root_dir,
#     static_path=_static_path,
#     output_path=_output_path,
#     network=_network_section,
# )

# _hazard = HazardSection(
#     hazard_field_name=["waterdepth"],
#     aggregate_wl=AggregateWlEnum.MEAN,
#     hazard_crs="EPSG:28992",
# )

# _section_damage = [
#     AnalysisSectionDamages(
#         name="Manual_damage",
#         analysis=AnalysisDamagesEnum.DAMAGES,
#         event_type=EventTypeEnum.EVENT,
#         damage_curve=DamageCurveEnum.MAN,
#         save_gpkg=True,
#         save_csv=True,
#     )
# ]

# _analysis_config_data = AnalysisConfigData(
#     analyses=_section_damage, root_path=_root_dir, output_path=_output_path
# )
# _analysis_config_data.input_path = _root_dir.joinpath("vulnerability_curves")

# # Run analysis
# _handler = Ra2ceHandler.from_config(_network_config_data, _analysis_config_data)
# _handler.input_config.network_config.config_data.hazard.hazard_map = [
#     list(_tif_data_directory.glob("*.tif"))[0]
# ]
# _handler.input_config.network_config.config_data.hazard.hazard_crs = "EPSG:28992"
# _handler.input_config.network_config.config_data.hazard.aggregate_wl = (
#     AggregateWlEnum.MAX
# )


# import warnings

# warnings.filterwarnings("ignore")

# _handler.configure()
# _handler.run_analysis()
