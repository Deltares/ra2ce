from ra2ce.configuration import AnalysisConfigBase, NetworkConfig
from ra2ce.ra2ce_input_config import Ra2ceInputConfig


class DummyNetworkConfig(NetworkConfig):
    def __init__(self) -> None:
        self.config_data = {}


class DummyAnalysisConfig(AnalysisConfigBase):
    def __init__(self) -> None:
        self.config_data = {}


class DummyRa2ceInput(Ra2ceInputConfig):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfig()
        self.network_config = DummyNetworkConfig()
