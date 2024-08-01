import random
import shutil
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionDamages, AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection, HazardSection, NetworkConfigData
from ra2ce.ra2ce_handler import Ra2ceHandler


# Create one network configuration per provided hazard.
# We assume the whole input directory will be mounted in `/modeldata`
_root_dir = Path("./modeldata")
assert _root_dir.exists()

# We assume the output graph of workflow 1 are mounted in the /output_graph_1 directory for the selected event_scenario
_output_1 = Path("./output_graph_1")
assert _output_1.exists()

# We also mount the vulnerability curves in the case we use predefined curves provided by users.
_vulnerability_data_directory = Path("./vulnerability_curves")
assert _vulnerability_data_directory


_static_path=_root_dir.joinpath("static")

_event_directory = list(_output_1.iterdir())[0]
assert _event_directory.exists()

_scenario_directory = list(_event_directory.iterdir())[0]
assert _scenario_directory.exists()

output_graph_1 = _scenario_directory.joinpath("output_graph")  # directory with the output graph from workflow 1
assert output_graph_1.exists()


print(_scenario_directory.stem)
print("\n")
# _selected_hazard_file = _hazard_files[0]

# Define output directory
output_path = _root_dir.joinpath("output")
assert output_path.exists()

_tif_data_directory = _static_path.joinpath("hazard")
assert _tif_data_directory.exists()

############### COPY files to the working directory #################

# Copy the output_graph files into the corresponding static directory:
destination_directory = _static_path.joinpath("output_graph")
#empty everything in the destination directory

for _file in destination_directory.iterdir():
    if _file.is_file():
        _file.unlink()

for _file in output_graph_1.iterdir():
    # copy the file into destination directory
    shutil.copy(_file, destination_directory)

_path_damage_data = _root_dir.joinpath("input_data", "damage_functions", "all_road_types")
assert _path_damage_data.exists()

# select a random vulnerability curve and copy it to working directory
_selected_vulnerability_curve = random.choice(list(_vulnerability_data_directory.glob("*.csv")))
shutil.copy(_selected_vulnerability_curve, _path_damage_data.joinpath("hazard_severity_damage fraction.csv"))

#################### Initialize the network configuration ####################


# Replacement for network ini:
_network_section = NetworkSection(
    source=SourceEnum.SHAPEFILE,       #Used to specify the shapefile name of the (road) network to do the analysis with, when creating a network from a shapefile.
    # primary_file=[_root_dir/"static"/"network"/"edges_NISv_RD_new_LinkNr.shp"], #specify in the RA2CE folder setup where the network is locates
    save_gpkg=True
)

#pass the specified sections as arguments for configuration
_network_section = NetworkSection(
    source=SourceEnum.SHAPEFILE,
    # primary_file=[
    #     _primary_file
    # ],
    file_id="rfid_c",
    save_gpkg=True,
)

# pass the specified sections as arguments for configuration
_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=_static_path,
    output_path=output_path,
    network=_network_section,
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
_analysis_config_data.input_path = _root_dir.joinpath("input_data")
assert _analysis_config_data.input_path.exists()

# Run analysis
_selected_hazard_file = _static_path.joinpath("hazard", "scenario_620.tif")
_handler = Ra2ceHandler.from_config(_network_config_data, _analysis_config_data)
_handler.input_config.network_config.config_data.hazard.hazard_map = [
    _selected_hazard_file
]
_handler.input_config.network_config.config_data.hazard.hazard_crs = "EPSG:28992"
_handler.input_config.network_config.config_data.hazard.aggregate_wl = (
    AggregateWlEnum.MAX
)

# Try to get only RELEVANT info messages.
import warnings

warnings.filterwarnings("ignore")

_handler.configure()
_handler.run_analysis()


# Copy static directory to output.
_static_output = output_path.joinpath("output_damage")
shutil.copytree(
    _static_path.joinpath("output_graph"), _static_output, dirs_exist_ok=True
)
