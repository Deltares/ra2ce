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

_hazard_files = list(_event_directory.glob("*.tif"))
print(_hazard_files)
print("\n")

_hazard_file = _hazard_files[0]
# To avoid overwritting during postprocessing
_output_name = _event_directory.name + "_" + _hazard_file.stem

# Define output directory
output_path = Path("/output_workflow1", "events", _event_directory.name)
output_path.mkdir(parents=True, exist_ok=True)
_dummy_file = output_path.joinpath(_hazard_file.name).with_suffix(".txt")
_dummy_file.touch()
_dummy_file.write_text("asdf")
