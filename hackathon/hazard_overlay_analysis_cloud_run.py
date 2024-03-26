import logging
from pathlib import Path

from ra2ce.ra2ce_handler import Ra2ceHandler

# Create one network configuration per provided hazard.
# We assume the whole input directory will be mounted in `/data`
_root_dir = Path("/data")
assert _root_dir.exists()

_network_file = _root_dir.joinpath("network.ini")
assert _network_file.exists()

_tif_data_directory = _root_dir.joinpath("data")
assert _tif_data_directory.exists()

_analysis_ini = _root_dir.joinpath("analysis.ini")
assert _analysis_ini.exists()

# Initialize logger.
# NOTE! Logging seems to flood the bucket files, so better to disable it for now.
# Ra2ceLogger(logging_dir=_network_data.output_path, logger_name="RA2CE")

# Run analysis
_handler = Ra2ceHandler(_network_file, _analysis_ini)
_handler.input_config.network_config.config_data.hazard.hazard_map = list(
    _tif_data_directory.glob("*.tif")
)

# Try to get only RELEVANT info messages.
import warnings

warnings.filterwarnings("ignore")

_handler.configure()
_handler.run_analysis()
