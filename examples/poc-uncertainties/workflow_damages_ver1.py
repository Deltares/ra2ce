
from pathlib import Path
import os
import random
import shutil

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionDamages, AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection, HazardSection, NetworkConfigData
from ra2ce.ra2ce_handler import Ra2ceHandler


vulnerability_curve_model = Path("C:/Users/gunaratn/RA2CE/RA2CE_Rep/ra2ce/examples/poc-uncertainties/vulnerability_curves")
_tif_data_directory = Path("C:/Users/gunaratn/RA2CE/RA2CE_Rep/ra2ce/examples/poc-uncertainties/flood_maps/event1")


_root_dir = Path("C:/Users/gunaratn/RA2CE/RA2CE_Rep/ra2ce/examples/poc-uncertainties/input_model")
static_path=_root_dir.joinpath("static")
vc = _root_dir.joinpath("vulnerability_curves/damage_functions/all_road_types")
output_path=_root_dir.joinpath("static/output_graph")
assert _root_dir.exists()


def copy_random_csv(source_folder, destination_folder):
    files = os.listdir(source_folder)
    csv_files = [file for file in files if file.endswith('.csv')]
    random_csv = random.choice(csv_files)
    source_file_path = os.path.join(source_folder, random_csv)
    destination_file_path = os.path.join(destination_folder, random_csv)

copy_random_csv(vulnerability_curve_model, vc)

#RA2CE RUN .......................................................................................
# Replacement for network ini:
_network_section = NetworkSection(
    source= SourceEnum.SHAPEFILE,       
    primary_file = [_root_dir/"static"/"network"/"motorway_osm.shp"], 
    file_id = "rfid_c",
    save_gpkg=True
)

#pass the specified sections as arguments for configuration
_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=static_path,
    output_path=output_path,
    network=_network_section,
    )

_hazard = HazardSection(
    hazard_field_name= ['waterdepth'],
    aggregate_wl = AggregateWlEnum.MEAN,
    hazard_crs = "EPSG:28992"
)

_section_damage = [AnalysisSectionDamages(
    name='Manual_damage',
    analysis=AnalysisDamagesEnum.DAMAGES,
    event_type=EventTypeEnum.EVENT,
    damage_curve=DamageCurveEnum.MAN,
    save_gpkg=True,
    save_csv=True,
)]

_analysis_config_data = AnalysisConfigData(analyses=_section_damage, root_path=_root_dir, output_path=output_path)
_analysis_config_data.input_path = _root_dir.joinpath("vulnerability_curves") 

print(_analysis_config_data.input_path)

# Run analysis
_handler = Ra2ceHandler.from_config(_network_config_data, _analysis_config_data)
_handler.input_config.network_config.config_data.hazard.hazard_map = [
    list(_tif_data_directory.glob("*.tif"))[0]
]
_handler.input_config.network_config.config_data.hazard.hazard_crs = "EPSG:28992"
_handler.input_config.network_config.config_data.hazard.aggregate_wl = AggregateWlEnum.MAX


import warnings

warnings.filterwarnings("ignore")

_handler.configure()
_handler.run_analysis()

