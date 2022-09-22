from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.configuration.network.network_ini_config_data import NetworkIniConfigData
from ra2ce.ra2ce_input_config import Ra2ceInputConfig


class DummyAnalysisConfig(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = {}


class DummyRa2ceInput(Ra2ceInputConfig):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfig()
        self.network_config = NetworkConfig()
