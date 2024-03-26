from pathlib import Path

from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.runners import AnalysisRunnerFactory
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.ra2ce_logging import Ra2ceLogger

# Create one network configuration per provided hazard.
_root_dir = Path(__file__).parent
_network_file = _root_dir.joinpath("network.ini")
assert _network_file.exists()
_network_data = NetworkConfigDataReader().read(_network_file)

_tif_data_directory = _root_dir.joinpath("data")
assert _tif_data_directory.exists()
_network_data.hazard.hazard_map = list(_tif_data_directory.glob("*.tif"))

# Create analysis wrapper
_analysis_ini = _root_dir.joinpath("analysis.ini")
assert _analysis_ini.exists()
_analysis_config_data = AnalysisConfigDataReader().read(_analysis_ini)


# Run one analysis per network hazard.
_config_wrapper = ConfigWrapper()

# Initialize logger.
Ra2ceLogger(logging_dir=_network_data.output_path, logger_name="RA2CE")

# Configure analysis and network
_network_config_wrapper = NetworkConfigWrapper.from_data(_network_file, _network_data)
_config_wrapper.network_config = _network_config_wrapper
_config_wrapper.analysis_config = AnalysisConfigWrapper.from_data_with_network(
    _analysis_ini, _analysis_config_data, _network_config_wrapper
)
_config_wrapper.configure()

# Run analysis
_runner = AnalysisRunnerFactory.get_runner(_config_wrapper)
_runner.run(_config_wrapper.analysis_config)
