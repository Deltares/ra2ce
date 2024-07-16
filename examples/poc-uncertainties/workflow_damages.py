

from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionDamages, AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection, HazardSection, NetworkConfigData
from ra2ce.ra2ce_handler import Ra2ceHandler

"""
    This script runs a network WITHOUT an analysis,
    as we are only interested to retrieve the HAZARD overlay.
"""

# Create one network configuration per provided hazard.
# We assume the whole input directory will be mounted in `/data`
_root_dir = Path("./input_model")
static_path=_root_dir.joinpath("static")
output_path=_root_dir.joinpath("output_workflow2/event1")

assert _root_dir.exists()

_tif_data_directory = Path("./flood_maps/event1")
_vulnerability_data_directory = Path("./vulnerability_curves")
assert _tif_data_directory.exists()


# Replacement for network ini:
_network_section = NetworkSection(
    source= SourceEnum.SHAPEFILE,       #Used to specify the shapefile name of the (road) network to do the analysis with, when creating a network from a shapefile.
    primary_file = [_root_dir/"static"/"network"/"edges_NISv_RD_new_LinkNr.shp"], #soecify in the RA2CE folder setup where the network is locates
    save_gpkg=True
)

#pass the specified sections as arguments for configuration
_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=static_path,
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
_analysis_config_data.input_path = _root_dir.joinpath("input_data") # TODO

# Run analysis
_handler = Ra2ceHandler.from_config(_network_config_data, _analysis_config_data)
_handler.input_config.network_config.config_data.hazard.hazard_map = [
    list(_tif_data_directory.glob("*.tif"))[0]
]
_handler.input_config.network_config.config_data.hazard.hazard_crs = "EPSG:28992"
_handler.input_config.network_config.config_data.hazard.aggregate_wl = AggregateWlEnum.MAX

# Try to get only RELEVANT info messages.
import warnings

warnings.filterwarnings("ignore")

# _handler.configure()
_handler.run_analysis()

