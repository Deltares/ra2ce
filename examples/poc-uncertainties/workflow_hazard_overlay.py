from pathlib import Path

from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.ra2ce_handler import Ra2ceHandler

"""
    This script runs a network WITHOUT an analysis,
    as we are only interested to retrieve the HAZARD overlay.
"""

# Create one network configuration per provided hazard.
# We assume the whole input directory will be mounted in `/data`
_root_dir = Path("/modeldata")
assert _root_dir.exists()
static_path = _root_dir.joinpath("static")


_events_data_directory = Path("/events")
assert _events_data_directory.exists()

_event_directory = list(_events_data_directory.iterdir())[0]
assert _event_directory.exists()

# Define output directory
output_path = Path("/output_workflow1", "events", _event_directory.name)
output_path.mkdir(parents=True, exist_ok=True)

# Replacement for network ini:
_primary_file = _root_dir.joinpath("static", "network", "edges_NISv_RD_new_LinkNr.shp")
assert _primary_file.exists()
_network_section = NetworkSection(
    source=SourceEnum.SHAPEFILE,  # Used to specify the shapefile name of the (road) network to do the analysis with, when creating a network from a shapefile.
    primary_file=[
        _primary_file
    ],  # soecify in the RA2CE folder setup where the network is locates
    save_gpkg=True,
)

# pass the specified sections as arguments for configuration
_network_config_data = NetworkConfigData(
    root_path=_root_dir,
    static_path=static_path,
    output_path=output_path,
    network=_network_section,
)

# Run analysis
_handler = Ra2ceHandler.from_config(_network_config_data, None)
_handler.input_config.network_config.config_data.hazard.hazard_map = [
    list(_event_directory.glob("*.tif"))[0]
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
