from pathlib import Path

from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from ra2ce.runners import AnalysisRunnerFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper

# This script runs a network WITHOUT an analysis,
# as we are only interested to retrieve the direct analysis.

# Create one network configuration per provided hazard.
_root_dir = Path("/data")
assert _root_dir.exists()

_network_file = _root_dir.joinpath("network.ini")
assert _network_file.exists()
_network_data = NetworkConfigDataReader().read(_network_file)

_tif_data_directory = _root_dir.joinpath("data")
assert _tif_data_directory.exists()
_network_data.hazard.hazard_map = list(_tif_data_directory.glob("*.tif"))

# Run one analysis per network hazard.
_config_wrapper = ConfigWrapper()

# Configure analysis and network
_network_config_wrapper = NetworkConfigWrapper.from_data(_network_file, _network_data)
_config_wrapper.network_config = _network_config_wrapper
_config_wrapper.configure()

# Run analysis
_runner = AnalysisRunnerFactory.get_runner(_config_wrapper)
_runner.run(_config_wrapper.analysis_config)
