import logging
from pathlib import Path

from ra2ce.ra2ce_handler import Ra2ceHandler

"""
    This script runs a network WITHOUT an analysis,
    as we are only interested to retrieve the HAZARD overlay.
"""

# Create one network configuration per provided hazard.
# We assume the whole input directory will be mounted in `/data`
_root_dir = Path("/data")
assert _root_dir.exists()

_network_file = _root_dir.joinpath("network.ini")
assert _network_file.exists()

_analysis_file = _root_dir.joinpath("analysis.ini")
assert _analysis_file.exists()

_tif_data_directory = Path("/input")
assert _tif_data_directory.exists()

# Run analysis
_handler = Ra2ceHandler(_network_file, _analysis_file)
_handler.input_config.network_config.config_data.hazard.hazard_map = [
    list(_tif_data_directory.glob("*.tif"))[0]
]

# Try to get only RELEVANT info messages.
import warnings

warnings.filterwarnings("ignore")

_handler.configure()
_handler.run_analysis()
